from __future__ import annotations
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from tg_agent.orchestrator import AgentOrchestrator
from tg_agent.tg_formatters import (
    format_markets_response,
    format_portfolio_response,
    format_analysis_response,
    format_error,
)
from tg_agent.keyboards import portfolio_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Welcome to Polymarket Broker!\n\n"
        "I can help you trade on prediction markets:\n"
        "- Search: 'bitcoin markets' or /markets bitcoin\n"
        "- Portfolio: /portfolio\n"
        "- AI Analysis: 'analyze BTC 120k market'\n"
        "- Trade: tap 'Trade' on any market result\n\n"
        "/bind YOUR_API_KEY to link your account\n"
        "/help for all commands"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Commands:\n"
        "/start - Welcome\n"
        "/markets [query] - Search markets\n"
        "/portfolio - Your positions\n"
        "/bind [api_key] - Link your account\n"
        "/help - This message\n\n"
        "Or just type naturally!"
    )


@router.message(Command("markets"))
async def cmd_markets(message: Message, orchestrator: AgentOrchestrator):
    query = message.text.replace("/markets", "").strip() or "trending"
    result = await orchestrator.invoke(
        capability="market_query",
        params={"action": "search", "query": query},
        user_id=str(message.from_user.id),
        context={"source": "telegram"},
    )
    text = format_markets_response(result) if result.get("success") else format_error(result)
    await message.answer(text)


@router.message(Command("portfolio"))
async def cmd_portfolio(message: Message, orchestrator: AgentOrchestrator, miniapp_url: str = ""):
    result = await orchestrator.invoke(
        capability="portfolio",
        params={"action": "positions"},
        user_id=str(message.from_user.id),
        context={"source": "telegram"},
    )
    text = format_portfolio_response(result) if result.get("success") else format_error(result)
    await message.answer(text, reply_markup=portfolio_keyboard(miniapp_url))


@router.message(F.text)
async def handle_text(message: Message, orchestrator: AgentOrchestrator):
    """Catch-all: parse natural language via orchestrator."""
    result = await orchestrator.handle_message(
        text=message.text,
        user_id=str(message.from_user.id),
        context={"source": "telegram", "chat_id": message.chat.id},
    )

    if not result.get("success"):
        await message.answer(format_error(result))
        return

    if "markets" in result:
        text = format_markets_response(result)
    elif "positions" in result or "balance" in result:
        text = format_portfolio_response(result)
    elif "answer" in result:
        text = format_analysis_response(result)
    else:
        text = str(result.get("data", result))

    await message.answer(text)


def create_bot(token: str) -> tuple[Bot, Dispatcher]:
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp
