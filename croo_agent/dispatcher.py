"""Croo event dispatcher → tg_agent capability invocation.

The Croo SDK's WebSocket dispatches events on its own thread (websockets library
runs the receive loop on a background thread). All work that touches SQLAlchemy
async sessions or our shared HTTP clients **must** run on the main asyncio loop.

The pattern used throughout this module:

  1. SDK fires `on_negotiation_created(event)` (sync, on SDK thread)
  2. We capture the main loop in __init__ and use `asyncio.run_coroutine_threadsafe`
     to schedule the actual async handler back onto it
  3. The future is stored in `self._inflight` so `drain()` can wait for graceful
     shutdown

Failure semantics:

  • Pre-accept validation errors (unknown service, bad requirement, disallowed
    sub-action) → `reject_negotiation(reason)` — buyer pays nothing
  • Post-accept failures (handler exception, timeout, success=False) → `deliver_order`
    with an error envelope, so the buyer always gets some response after paying
"""
from __future__ import annotations

import asyncio
import logging
from concurrent.futures import Future
from typing import Any

from croo_agent.deliverables import build_envelope, envelope_to_text
from croo_agent.services import (
    RequirementValidationError,
    ServiceSpec,
    merge_params,
    parse_requirement,
    validate_against_binding,
    validate_requirement,
)

logger = logging.getLogger(__name__)


class CrooDispatcher:
    """Bridges Croo SDK WebSocket events to tg_agent.orchestrator.invoke()."""

    def __init__(
        self,
        *,
        agent_client,
        orchestrator,
        context_provider,
        service_map: dict[str, ServiceSpec],
        main_loop: asyncio.AbstractEventLoop,
        system_user_id: str,
        timeout_default_s: int,
        timeout_overrides: dict[str, int] | None = None,
        dry_run: bool = False,
    ):
        self._agent_client = agent_client
        self._orchestrator = orchestrator
        self._context_provider = context_provider
        # service_id → ServiceSpec (full binding incl. capability + preset_params)
        self._service_map = service_map
        self._main_loop = main_loop
        self._system_user_id = system_user_id
        self._timeout_default_s = timeout_default_s
        self._timeout_overrides = timeout_overrides or {}
        self._dry_run = dry_run

        # Cache of order_id → (capability, validated requirement) populated when we
        # accept a negotiation. ORDER_PAID events don't carry requirement data, so we
        # need to remember it from accept-time.
        self._pending: dict[str, tuple[str, dict]] = {}
        self._pending_lock = asyncio.Lock()

        # Track in-flight tasks so drain() can wait for them
        self._inflight: set[asyncio.Task] = set()

    # ── public API ──────────────────────────────────────────────────────────

    def register_listeners(self, stream) -> None:
        """Wire up the listeners on a `croo.EventStream` instance."""
        from croo import EventType

        stream.on(EventType.NEGOTIATION_CREATED, self._on_negotiation_created)
        stream.on(EventType.ORDER_PAID, self._on_order_paid)
        stream.on(EventType.ORDER_COMPLETED, self._on_order_completed_log)
        stream.on(EventType.ORDER_REJECTED, self._on_order_rejected_log)
        stream.on(EventType.ORDER_EXPIRED, self._on_order_expired_log)
        logger.info(
            "CrooDispatcher listeners registered (services=%d, dry_run=%s)",
            len(self._service_map), self._dry_run,
        )

    async def drain(self, timeout: float = 30.0) -> None:
        """Wait for all in-flight handlers to finish, with a hard timeout."""
        if not self._inflight:
            return
        logger.info("Draining %d in-flight Croo task(s) (timeout=%.0fs)", len(self._inflight), timeout)
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._inflight, return_exceptions=True),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("Drain timeout — %d task(s) still in-flight", len(self._inflight))

    # ── sync callbacks (run on SDK thread) ──────────────────────────────────

    def _on_negotiation_created(self, event) -> None:
        try:
            asyncio.run_coroutine_threadsafe(
                self._handle_negotiation(event), self._main_loop,
            )
        except Exception:
            logger.exception("Failed to schedule negotiation handler for %s", getattr(event, "negotiation_id", "?"))

    def _on_order_paid(self, event) -> None:
        try:
            asyncio.run_coroutine_threadsafe(
                self._handle_paid_order(event), self._main_loop,
            )
        except Exception:
            logger.exception("Failed to schedule paid-order handler for %s", getattr(event, "order_id", "?"))

    def _on_order_completed_log(self, event) -> None:
        logger.info("ORDER_COMPLETED order_id=%s", getattr(event, "order_id", "?"))

    def _on_order_rejected_log(self, event) -> None:
        logger.info("ORDER_REJECTED order_id=%s reason=%s", getattr(event, "order_id", "?"), getattr(event, "reason", ""))

    def _on_order_expired_log(self, event) -> None:
        logger.warning("ORDER_EXPIRED order_id=%s", getattr(event, "order_id", "?"))

    # ── async handlers (run on main loop) ───────────────────────────────────

    def _spawn_tracked(self, coro) -> asyncio.Task:
        task = asyncio.create_task(coro)
        self._inflight.add(task)
        task.add_done_callback(self._inflight.discard)
        return task

    async def _handle_negotiation(self, event) -> None:
        """Validate and accept-or-reject an incoming negotiation.

        Per-service binding pipeline:
          1. Look up `ServiceSpec` by `service_id` in `self._service_map`
          2. Parse buyer requirements JSON
          3. `validate_against_binding(spec, buyer_req)` — checks `extra_required`,
             rejects unknown fields, refuses to let buyer override `preset_params`
          4. `merge_params(spec, buyer_req)` — yields the final params dict the
             handler will see, with the seller-controlled `preset_params` always
             taking precedence
          5. `validate_requirement(spec.capability, final_params)` — second-line
             defence at the capability level (legacy contract)
          6. `accept_negotiation` and cache (capability, final_params) for the
             upcoming ORDER_PAID event
        """
        negotiation_id = getattr(event, "negotiation_id", "")
        service_id = getattr(event, "service_id", "")
        if not negotiation_id:
            logger.warning("NEGOTIATION_CREATED with empty negotiation_id, ignoring")
            return

        spec = self._service_map.get(service_id)
        if spec is None:
            logger.warning("Unknown service_id=%s for negotiation %s; rejecting", service_id, negotiation_id)
            await self._safe_reject_negotiation(
                negotiation_id, f"unknown service_id {service_id}",
            )
            return

        # Fetch the negotiation to read the buyer's `requirements` JSON.
        try:
            negotiation = await self._agent_client.get_negotiation(negotiation_id)
        except Exception as exc:
            logger.exception("get_negotiation(%s) failed", negotiation_id)
            await self._safe_reject_negotiation(negotiation_id, f"could not fetch negotiation: {exc}")
            return

        try:
            buyer_req = parse_requirement(getattr(negotiation, "requirements", ""))
            validate_against_binding(spec, buyer_req)
            final_params = merge_params(spec, buyer_req)
            validate_requirement(spec.capability, final_params)
        except RequirementValidationError as exc:
            logger.info(
                "Rejecting negotiation %s (service=%s slug=%s) — invalid requirement: %s",
                negotiation_id, service_id, spec.slug, exc,
            )
            await self._safe_reject_negotiation(negotiation_id, str(exc))
            return
        except Exception as exc:
            logger.exception("Unexpected validation error for negotiation %s", negotiation_id)
            await self._safe_reject_negotiation(negotiation_id, f"validation error: {exc}")
            return

        # Accept on-chain. The result has the new order_id we cache for later.
        try:
            accept_result = await self._agent_client.accept_negotiation(negotiation_id)
        except Exception as exc:
            logger.exception("accept_negotiation(%s) failed", negotiation_id)
            return  # nothing else we can do — buyer's negotiation will eventually expire

        order = getattr(accept_result, "order", None)
        order_id = getattr(order, "order_id", "") if order else ""
        if not order_id:
            logger.error("accept_negotiation %s returned no order_id", negotiation_id)
            return

        async with self._pending_lock:
            self._pending[order_id] = (spec.capability, final_params)
        logger.info(
            "Accepted negotiation %s → order %s (slug=%s capability=%s preset=%s)",
            negotiation_id, order_id, spec.slug, spec.capability, spec.preset_params,
        )

    async def _handle_paid_order(self, event) -> None:
        """Resolve the cached requirement, run the handler, deliver the envelope."""
        order_id = getattr(event, "order_id", "")
        if not order_id:
            logger.warning("ORDER_PAID with empty order_id, ignoring")
            return

        async with self._pending_lock:
            cached = self._pending.pop(order_id, None)

        if cached is None:
            # Could happen on restart with in-flight orders — try to recover via the API.
            logger.warning("ORDER_PAID for unknown order %s; attempting recovery", order_id)
            cached = await self._recover_order_context(order_id)
            if cached is None:
                logger.error("Could not recover context for order %s; refusing to deliver", order_id)
                return

        capability, validated = cached
        # Spawn as a tracked task so the dispatcher's caller can return immediately
        # and drain() can wait for completion.
        self._spawn_tracked(self._run_and_deliver(order_id, capability, validated))

    async def _recover_order_context(self, order_id: str) -> tuple[str, dict] | None:
        """If we restarted with in-flight orders, refetch what we need from the API.

        Best-effort: we can identify the right capability via the order's service_id,
        but we have no way to recover the original buyer requirements (Order doesn't
        carry them and there's no order→negotiation lookup in the SDK we've seen).
        We deliver a `_recovered: true` envelope so the buyer at least gets a response.
        """
        try:
            order = await self._agent_client.get_order(order_id)
        except Exception:
            logger.exception("get_order(%s) failed during recovery", order_id)
            return None

        service_id = getattr(order, "service_id", "")
        spec = self._service_map.get(service_id)
        if spec is None:
            logger.error("Recovery: unknown service_id %s for order %s", service_id, order_id)
            return None

        # Synthesize a minimal params dict from the preset alone — extra_required
        # fields will be missing, so most handlers will return success=False or raise.
        # That's intentional: a recovered order is delivered with an error envelope.
        recovered_params = {**spec.preset_params, "_recovered": True}
        return spec.capability, recovered_params

    async def _run_and_deliver(self, order_id: str, capability: str, params: dict) -> None:
        """Run the handler under timeout and call deliver_order with the envelope."""
        timeout = self._timeout_overrides.get(capability, self._timeout_default_s)

        context = None
        envelope: dict
        try:
            context = await self._context_provider.get_context()
            try:
                handler_result = await asyncio.wait_for(
                    self._orchestrator.invoke(
                        capability=capability,
                        params=params,
                        user_id=self._system_user_id,
                        context=context,
                    ),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                logger.warning("Handler timeout (%ds) for order %s capability=%s", timeout, order_id, capability)
                envelope = build_envelope(
                    service=capability, order_id=order_id, request=params,
                    error=("HANDLER_TIMEOUT", f"handler exceeded {timeout}s"),
                )
            except Exception as exc:
                logger.exception("Handler raised for order %s capability=%s", order_id, capability)
                envelope = build_envelope(
                    service=capability, order_id=order_id, request=params,
                    error=("HANDLER_EXCEPTION", str(exc)),
                )
            else:
                if not isinstance(handler_result, dict):
                    handler_result = {"success": True, "value": handler_result}
                envelope = build_envelope(
                    service=capability, order_id=order_id, request=params,
                    result=handler_result,
                )
        finally:
            if context is not None:
                try:
                    await self._context_provider.cleanup_context(context)
                except Exception:
                    logger.exception("cleanup_context failed for order %s", order_id)

        await self._safe_deliver(order_id, capability, envelope)

    # ── delivery helpers (idempotent + log on failure) ──────────────────────

    async def _safe_deliver(self, order_id: str, capability: str, envelope: dict) -> None:
        from croo import DeliverableType, DeliverOrderRequest

        text = envelope_to_text(envelope)
        if self._dry_run:
            logger.info(
                "[dry-run] would deliver_order(%s) capability=%s status=%s bytes=%d",
                order_id, capability, envelope.get("status"), len(text.encode("utf-8")),
            )
            return
        try:
            await self._agent_client.deliver_order(
                order_id,
                DeliverOrderRequest(deliverable_type=DeliverableType.TEXT, deliverable_text=text),
            )
            logger.info(
                "Delivered order %s capability=%s status=%s bytes=%d",
                order_id, capability, envelope.get("status"), len(text.encode("utf-8")),
            )
        except Exception:
            logger.exception("deliver_order(%s) failed", order_id)

    async def _safe_reject_negotiation(self, negotiation_id: str, reason: str) -> None:
        try:
            await self._agent_client.reject_negotiation(negotiation_id, reason)
        except Exception:
            logger.exception("reject_negotiation(%s) failed", negotiation_id)
