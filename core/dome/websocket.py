"""Dome WebSocket manager for real-time order and activity streaming."""

import asyncio
import json
import logging
from typing import Any, Callable, Awaitable

import websockets
from websockets.asyncio.client import ClientConnection

from core.dome.key_pool import DomeKeyPool

logger = logging.getLogger(__name__)

_WS_BASE = "wss://ws.domeapi.io"
_MAX_BACKOFF = 60.0

# Callback type: async def handler(message: dict) -> None
Handler = Callable[[dict], Awaitable[None]]


class DomeWebSocketManager:
    """Manages a persistent WebSocket connection to Dome.

    Handles:
    - Auto-reconnect with exponential backoff
    - Subscription management (subscribe / unsubscribe)
    - Re-subscribe on reconnect
    - Message dispatch to registered handlers
    """

    def __init__(self, key_pool: DomeKeyPool):
        self._pool = key_pool
        self._conn: ClientConnection | None = None
        self._handlers: dict[str, Handler] = {}  # type -> handler
        # Tracks active subscriptions for re-subscribe on reconnect.
        # subscription_id -> original subscribe payload
        self._subscriptions: dict[str, dict] = {}
        # Pending subscribe payloads (before first subscription_id is assigned).
        self._pending_subs: list[dict] = []
        self._running = False
        self._task: asyncio.Task | None = None

    # ── lifecycle ────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the WebSocket message pump in a background task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("dome websocket manager started")

    async def stop(self) -> None:
        """Gracefully close the connection and cancel the pump task."""
        self._running = False
        if self._conn:
            await self._conn.close()
            self._conn = None
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("dome websocket manager stopped")

    # ── subscription API ─────────────────────────────────────────

    def on(self, message_type: str, handler: Handler) -> None:
        """Register *handler* for messages of *message_type* (e.g., 'orders')."""
        self._handlers[message_type] = handler

    async def subscribe_orders(
        self,
        *,
        condition_ids: list[str] | None = None,
        users: list[str] | None = None,
        market_slugs: list[str] | None = None,
    ) -> None:
        """Subscribe to real-time order updates."""
        filters: dict[str, Any] = {}
        if condition_ids:
            filters["condition_ids"] = condition_ids
        if users:
            filters["users"] = users
        if market_slugs:
            filters["market_slugs"] = market_slugs
        # If no filters, subscribe to everything.
        if not filters:
            filters["users"] = ["*"]
        payload = {
            "action": "subscribe",
            "platform": "polymarket",
            "version": 1,
            "type": "orders",
            "filters": filters,
        }
        await self._send(payload)
        self._pending_subs.append(payload)

    async def unsubscribe(self, subscription_id: str) -> None:
        payload = {"action": "unsubscribe", "subscription_id": subscription_id}
        await self._send(payload)
        self._subscriptions.pop(subscription_id, None)

    # ── internals ────────────────────────────────────────────────

    async def _send(self, payload: dict) -> None:
        if self._conn:
            await self._conn.send(json.dumps(payload))

    async def _connect(self) -> ClientConnection:
        key = self._pool.next_ws_key()
        url = f"{_WS_BASE}/{key}"
        conn = await websockets.connect(url)
        logger.info("dome websocket connected")
        return conn

    async def _resubscribe(self) -> None:
        """Re-send all tracked subscriptions after a reconnect."""
        for payload in self._subscriptions.values():
            await self._send(payload)
        for payload in self._pending_subs:
            await self._send(payload)

    async def _run_loop(self) -> None:
        backoff = 1.0
        while self._running:
            try:
                self._conn = await self._connect()
                backoff = 1.0  # reset on success
                await self._resubscribe()
                async for raw in self._conn:
                    msg = json.loads(raw)
                    self._handle_system(msg)
                    msg_type = msg.get("type")
                    handler = self._handlers.get(msg_type)
                    if handler:
                        try:
                            await handler(msg)
                        except Exception:
                            logger.exception("dome ws handler error for type=%s", msg_type)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("dome websocket error, reconnecting in %.0fs", backoff)
            finally:
                if self._conn:
                    await self._conn.close()
                    self._conn = None
            if self._running:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, _MAX_BACKOFF)

    def _handle_system(self, msg: dict) -> None:
        """Track subscription confirmations from the server."""
        sub_id = msg.get("subscription_id")
        if sub_id and msg.get("action") == "subscribed":
            # Move from pending to confirmed.
            if self._pending_subs:
                original = self._pending_subs.pop(0)
                self._subscriptions[sub_id] = original
                logger.info("dome ws subscription confirmed: %s", sub_id)
