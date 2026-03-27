from __future__ import annotations
import logging
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

Handler = Callable[..., Awaitable[dict]]

CONFIDENCE_THRESHOLD = 0.6


class AgentOrchestrator:
    """Routes both NL messages and structured invocations to capability handlers."""

    def __init__(self, intent_parser: Any) -> None:
        self._parser = intent_parser
        self._handlers: dict[str, Handler] = {}

    def register_handler(self, capability: str, handler: Handler) -> None:
        self._handlers[capability] = handler

    async def handle_message(
        self,
        text: str,
        user_id: str,
        context: dict,
    ) -> dict:
        """Parse NL message -> route to capability handler."""
        intent = await self._parser.parse(text)
        capability = intent.get("capability", "unknown")
        confidence = intent.get("confidence", 0.0)

        if capability == "unknown" or confidence < CONFIDENCE_THRESHOLD:
            return {
                "success": False,
                "error": "I don't understand that request. Please clarify -- you can ask about markets, orders, portfolio, or analysis.",
            }

        return await self.invoke(
            capability=capability,
            params=intent.get("params", {}),
            user_id=user_id,
            context=context,
        )

    async def invoke(
        self,
        capability: str,
        params: dict,
        user_id: str,
        context: dict,
    ) -> dict:
        """Direct structured invocation (for A2A calls)."""
        handler = self._handlers.get(capability)
        if not handler:
            return {"success": False, "error": f"Unknown capability: {capability}"}

        try:
            return await handler(params=params, user_id=user_id, context=context)
        except Exception as exc:
            logger.exception("handler %s failed", capability)
            return {"success": False, "error": str(exc)}
