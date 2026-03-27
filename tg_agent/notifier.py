from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot: Any) -> None:
        self._bot = bot

    async def notify(self, chat_id: int, event: str, data: dict) -> None:
        text = self._format(event, data)
        try:
            await self._bot.send_message(chat_id=chat_id, text=text)
        except Exception:
            logger.warning("failed to send TG notification to %s", chat_id, exc_info=True)

    def _format(self, event: str, data: dict) -> str:
        formatters = {
            "order.filled": self._fmt_order_filled,
            "order.cancelled": self._fmt_order_cancelled,
            "market.resolved": self._fmt_market_resolved,
        }
        return formatters.get(event, self._fmt_generic)(data)

    def _fmt_order_filled(self, d: dict) -> str:
        return (
            f"Order Filled\n"
            f"{d.get('side', '?')} x{d.get('size', '?')} @ ${d.get('price', '?')}\n"
            f"Order: {d.get('order_id', '?')}"
        )

    def _fmt_order_cancelled(self, d: dict) -> str:
        return f"Order Cancelled\nOrder: {d.get('order_id', '?')}"

    def _fmt_market_resolved(self, d: dict) -> str:
        return f"Market Resolved\n{d.get('question', '?')}\nOutcome: {d.get('outcome', '?')}"

    def _fmt_generic(self, d: dict) -> str:
        return f"Notification\n{d}"
