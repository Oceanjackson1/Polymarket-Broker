"""Croo Provider runtime — connects the AgentClient WebSocket and dispatches events.

Mirrors `tg_agent/cli.py` for infra bootstrap (DB, Redis, Dome, Gamma) but produces
no Telegram bot — instead it builds a `CrooDispatcher` and waits for events.

Entry: `python -m croo_agent`  →  `croo_agent.cli.main` → `runtime.run_provider()`
"""
from __future__ import annotations

import asyncio
import logging
import signal
import sys
from typing import Any

import httpx

from core.config import get_settings
from croo_agent import credentials as creds_mod
from croo_agent.dispatcher import CrooDispatcher

logger = logging.getLogger(__name__)


async def _feilian_check(base_url: str, timeout_s: float = 5.0) -> bool:
    """Best-effort connectivity check against the Croo dev API.

    Tries the base URL itself; any HTTP response (even 404) means we have IP-level
    reachability through Feilian. Only network/DNS failures count as a failure.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.get(base_url)
            logger.info("Feilian check ok (HTTP %d from %s)", resp.status_code, base_url)
            return True
    except Exception as exc:
        logger.error(
            "Feilian check FAILED for %s: %s. Is the Feilian VPN connected?",
            base_url, exc,
        )
        return False


async def _build_orchestrator_for_croo():
    """Construct the same orchestrator tg_agent uses, with a dummy DeepSeek client.

    The DeepSeek/AsyncOpenAI instance is required by `build_orchestrator` for the
    intent_parser path used by Telegram, but Croo invokes the orchestrator via
    `invoke()` directly — the parser is never triggered, so the client is unused at
    runtime.
    """
    from openai import AsyncOpenAI
    from tg_agent.factory import build_orchestrator

    settings = get_settings()
    ai_client = AsyncOpenAI(
        api_key=settings.deepseek_api_key or "unused-by-croo",
        base_url=settings.deepseek_base_url,
    )
    return build_orchestrator(ai_client=ai_client, model=settings.deepseek_model)


async def run_provider(check_only: bool = False, dry_run: bool = False) -> int:
    """Main runtime entry. Returns process exit code."""
    settings = get_settings()

    # 1. Feilian connectivity (fail-fast)
    if not await _feilian_check(settings.croo_api_base):
        return 3

    if check_only:
        print("OK")
        return 0

    # 2. Load credentials (file first, env fallback)
    try:
        creds = creds_mod.load_with_env_fallback()
    except creds_mod.CredentialsMissing as exc:
        logger.error("Cannot start Croo provider: %s", exc)
        logger.error("Run `python -m croo_agent.setup_cli` to bootstrap credentials.")
        return 4

    if not creds.services:
        logger.error(
            "Credentials have no service_id → capability mapping. Either re-run "
            "`python -m croo_agent.setup_cli` or populate the JSON file manually."
        )
        return 5

    # 3. Initialise shared infrastructure (mirrors tg_agent/cli.py)
    from db.postgres import init_db, engine as db_engine
    from db.redis_client import get_redis_pool

    logger.info("Initialising shared infrastructure (db, redis, gamma, dome)…")
    await init_db()
    redis = await get_redis_pool()

    dome_client = None
    try:
        from core.dome.factory import build_dome_key_pool, build_dome_client
        pool = build_dome_key_pool()
        if pool:
            dome_client = build_dome_client(pool)
            logger.info("Dome client initialised")
    except Exception:
        logger.warning("Dome client not available", exc_info=True)

    from core.polymarket.gamma_client import GammaClient
    gamma_client = GammaClient()

    from tg_agent.context import TgContextProvider
    context_provider = TgContextProvider(
        dome_client=dome_client,
        redis=redis,
        gamma_client=gamma_client,
    )

    orchestrator = await _build_orchestrator_for_croo()

    # 4. Croo AgentClient
    from croo import AgentClient, Config

    agent_client = AgentClient(
        Config(
            base_url=settings.croo_api_base,
            ws_url=settings.croo_ws_url,
            rpc_url=settings.croo_rpc_url,
        ),
        creds.sdk_key,
    )

    # Resolve the credentials.services map (service_id → slug) into the live
    # ServiceSpec bindings the dispatcher needs. Drop entries with unknown slugs
    # so a partially-broken catalogue still starts (with reduced surface area).
    from croo_agent.services import SPECS_BY_SLUG

    service_map: dict = {}
    unknown_slugs: list[tuple[str, str]] = []
    for sid, slug in creds.services.items():
        spec = SPECS_BY_SLUG.get(slug)
        if spec is None:
            unknown_slugs.append((sid, slug))
            continue
        service_map[sid] = spec

    if unknown_slugs:
        logger.warning(
            "Dropping %d service(s) with unknown slugs (rerun setup_cli --rebuild "
            "to refresh): %s",
            len(unknown_slugs),
            [slug for _, slug in unknown_slugs],
        )

    if not service_map:
        logger.error(
            "No services resolved from credentials. Either the catalogue is empty "
            "or your .credentials.json is from an older schema (v1 capability names). "
            "Run `python -m croo_agent.setup_cli --rebuild` to upgrade."
        )
        return 6

    main_loop = asyncio.get_running_loop()
    timeout_overrides = {
        "analysis": settings.croo_handler_timeout_analysis_s,
        "strategy": settings.croo_handler_timeout_strategy_s,
    }
    dispatcher = CrooDispatcher(
        agent_client=agent_client,
        orchestrator=orchestrator,
        context_provider=context_provider,
        service_map=service_map,
        main_loop=main_loop,
        system_user_id=settings.croo_system_user_id,
        timeout_default_s=settings.croo_handler_timeout_default_s,
        timeout_overrides=timeout_overrides,
        dry_run=dry_run,
    )

    # 5. Connect WebSocket and register listeners
    logger.info("Connecting Croo WebSocket: %s", settings.croo_ws_url)
    stream = await agent_client.connect_websocket()
    dispatcher.register_listeners(stream)

    services_summary = ", ".join(sorted(spec.slug for spec in service_map.values()))
    logger.info(
        "Provider live: agent_id=%s, wallet=%s, services=[%s]%s",
        creds.agent_id, creds.wallet_address, services_summary,
        " (dry-run)" if dry_run else "",
    )

    # 6. Wait for shutdown signal
    shutdown_event = asyncio.Event()
    _install_signal_handlers(main_loop, shutdown_event)
    try:
        await shutdown_event.wait()
    except asyncio.CancelledError:
        pass

    # 7. Graceful shutdown
    logger.info("Shutdown initiated; draining in-flight tasks…")
    await dispatcher.drain(timeout=30.0)

    logger.info("Closing Croo WebSocket")
    try:
        await stream.close()
    except Exception:
        logger.exception("Error closing Croo EventStream")

    try:
        await agent_client.close()
    except Exception:
        logger.exception("Error closing Croo AgentClient")

    logger.info("Closing infra clients")
    try:
        await gamma_client.close()
    except Exception:
        logger.exception("Error closing GammaClient")
    if dome_client is not None:
        try:
            await dome_client.close()
        except Exception:
            logger.exception("Error closing DomeClient")
    try:
        await redis.aclose()
    except Exception:
        logger.exception("Error closing Redis pool")
    try:
        await db_engine.dispose()
    except Exception:
        logger.exception("Error disposing DB engine")

    logger.info("Croo provider shut down cleanly")
    return 0


def _install_signal_handlers(loop: asyncio.AbstractEventLoop, event: asyncio.Event) -> None:
    """Install SIGINT/SIGTERM handlers that set the shutdown event."""

    def _trigger():
        if not event.is_set():
            logger.info("Received shutdown signal")
            event.set()

    if sys.platform == "win32":
        # loop.add_signal_handler is unsupported on Windows
        signal.signal(signal.SIGINT, lambda *_: loop.call_soon_threadsafe(_trigger))
        signal.signal(signal.SIGTERM, lambda *_: loop.call_soon_threadsafe(_trigger))
        return

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _trigger)
        except (NotImplementedError, RuntimeError):
            signal.signal(sig, lambda *_: loop.call_soon_threadsafe(_trigger))
