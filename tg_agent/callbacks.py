from __future__ import annotations
import logging
from aiogram import Router
from aiogram.types import CallbackQuery
from tg_agent.orchestrator import AgentOrchestrator
from tg_agent.tg_formatters import format_analysis_response, format_error

logger = logging.getLogger(__name__)
router = Router()


def parse_callback_data(data: str) -> dict:
    """Parse callback_data string into structured dict."""
    parts = data.split(":")

    if parts[0] == "quick" and len(parts) == 5:
        return {
            "action": "quick",
            "condition_id": parts[1],
            "side": parts[2],
            "price": float(parts[3]),
            "amount": float(parts[4]),
        }

    if parts[0] in ("analyze", "orderbook", "buy_yes", "buy_no") and len(parts) == 2:
        return {"action": parts[0], "condition_id": parts[1]}

    if parts[0] in ("confirm",) and len(parts) == 2:
        return {"action": parts[0], "key": parts[1]}

    return {"action": data}


@router.callback_query(lambda c: c.data and c.data.startswith("analyze:"))
async def cb_analyze(callback: CallbackQuery, orchestrator: AgentOrchestrator):
    parsed = parse_callback_data(callback.data)
    await callback.answer("Analyzing...")

    result = await orchestrator.invoke(
        capability="analysis",
        params={"action": "market", "market_id": parsed["condition_id"]},
        user_id=str(callback.from_user.id),
        context={"source": "telegram"},
    )
    text = format_analysis_response(result) if result.get("success") else format_error(result)
    await callback.message.answer(text)


@router.callback_query(lambda c: c.data and c.data.startswith("quick:"))
async def cb_quick_order(callback: CallbackQuery, orchestrator: AgentOrchestrator):
    parsed = parse_callback_data(callback.data)
    size = parsed["amount"] / parsed["price"]

    await callback.answer("Placing order...")

    result = await orchestrator.invoke(
        capability="place_order",
        params={
            "token_id": parsed["condition_id"],
            "side": parsed["side"],
            "price": parsed["price"],
            "size": round(size, 2),
        },
        user_id=str(callback.from_user.id),
        context={"source": "telegram"},
    )

    if result.get("success"):
        await callback.message.answer(
            f"Order placed!\n"
            f"{parsed['side']} x{round(size, 2)} @ ${parsed['price']}\n"
            f"Total: ${parsed['amount']}"
        )
    else:
        await callback.message.answer(format_error(result))


@router.callback_query(lambda c: c.data == "cancel_action")
async def cb_cancel(callback: CallbackQuery):
    await callback.answer("Cancelled")
    await callback.message.edit_text("Action cancelled.")


@router.callback_query(lambda c: c.data == "portfolio:refresh")
async def cb_portfolio_refresh(callback: CallbackQuery, orchestrator: AgentOrchestrator):
    await callback.answer("Refreshing...")
    result = await orchestrator.invoke(
        capability="portfolio",
        params={"action": "positions"},
        user_id=str(callback.from_user.id),
        context={"source": "telegram"},
    )
    from tg_agent.tg_formatters import format_portfolio_response
    text = format_portfolio_response(result) if result.get("success") else format_error(result)
    await callback.message.edit_text(text)
