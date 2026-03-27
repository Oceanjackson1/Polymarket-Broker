from __future__ import annotations
import logging
from fastapi import APIRouter, Request, Response
from aiogram.types import Update

logger = logging.getLogger(__name__)
router = APIRouter(tags=["telegram-webhook"])


def verify_webhook_secret(expected: str, received: str) -> bool:
    if not expected and not received:
        return True
    return expected == received


@router.post("/api/v1/agent/tg-webhook")
async def telegram_webhook(request: Request):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    expected = getattr(request.app.state, "tg_webhook_secret", "")
    if not verify_webhook_secret(expected, secret):
        return Response(status_code=403)
    bot = request.app.state.tg_bot
    dp = request.app.state.tg_dispatcher
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot=bot, update=update)
    return Response(status_code=200)
