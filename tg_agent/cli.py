"""Run TG bot in polling mode for local development.
Usage: python -m tg_agent
"""
from __future__ import annotations
import asyncio
import logging
from core.config import get_settings
from tg_agent.bot import create_bot
from tg_agent.factory import build_orchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    settings = get_settings()
    if not settings.tg_bot_token:
        logger.error("TG_BOT_TOKEN not set in .env")
        return

    from openai import AsyncOpenAI
    ai_client = AsyncOpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )

    orchestrator = build_orchestrator(ai_client=ai_client, model=settings.deepseek_model)
    bot, dp = create_bot(settings.tg_bot_token)
    dp["orchestrator"] = orchestrator
    dp["miniapp_url"] = settings.tg_miniapp_url

    logger.info("Starting TG bot in polling mode...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
