from __future__ import annotations
import hmac
import hashlib
import json
import time
from urllib.parse import unquote
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/agent", tags=["agent-auth"])


class TgAuthRequest(BaseModel):
    init_data: str


class TgAuthResponse(BaseModel):
    access_token: str
    user_id: str
    tg_user_id: int


def parse_init_data(init_data: str) -> dict:
    """Parse Telegram WebApp initData query string."""
    result = {}
    for part in init_data.split("&"):
        if "=" in part:
            key, val = part.split("=", 1)
            result[key] = unquote(val)
    return result


def validate_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 86400,
) -> dict | None:
    """Validate Telegram WebApp initData HMAC signature.
    Returns parsed user data or None if invalid."""
    parsed = parse_init_data(init_data)
    received_hash = parsed.pop("hash", "")

    # Check expiry
    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > max_age_seconds:
        return None

    # Build data-check-string (sorted key=value pairs)
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    # HMAC-SHA256 with secret = HMAC-SHA256("WebAppData", bot_token)
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed, received_hash):
        return None

    # Parse user JSON
    user_str = parsed.get("user", "{}")
    try:
        user = json.loads(user_str)
    except json.JSONDecodeError:
        return None

    return {"tg_user_id": user.get("id"), "username": user.get("username", "")}


@router.post("/tg-auth", response_model=TgAuthResponse)
async def tg_miniapp_auth(body: TgAuthRequest):
    """Exchange Telegram Mini App initData for a JWT access token."""
    from core.config import get_settings
    settings = get_settings()

    user_data = validate_init_data(body.init_data, settings.tg_bot_token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired Telegram auth")

    tg_user_id = user_data["tg_user_id"]

    # Look up linked broker account
    from db.postgres import AsyncSessionLocal
    from tg_agent.auth import get_user_id_by_chat

    async with AsyncSessionLocal() as db:
        user_id = await get_user_id_by_chat(db, tg_user_id)

    if not user_id:
        raise HTTPException(status_code=403, detail="No linked account. Use /bind in the bot first.")

    # Issue JWT
    from api.auth.service import AuthService
    async with AsyncSessionLocal() as db:
        auth_svc = AuthService(db)
        token = auth_svc.create_access_token(user_id)

    return TgAuthResponse(
        access_token=token,
        user_id=user_id,
        tg_user_id=tg_user_id,
    )
