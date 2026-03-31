from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis
from typing import Optional

from db.postgres import get_session
from db.redis_client import get_redis
from api.deps import get_current_user_id, get_current_user_from_api_key
from api.auth.service import AuthService
from api.auth.models import User
from api.auth.schemas import (
    TokenResponse, UserResponse,
    ApiKeyCreateRequest, ApiKeyCreatedResponse, ApiKeyListItem,
)
from core.security import decode_access_token
from core.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

ALL_SCOPES = [
    "data:read", "markets:read", "orders:write", "portfolio:read",
    "analysis:read", "strategies:execute", "webhooks:write",
]


async def _resolve_user_id_flexible(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_session),
) -> str:
    """Accept either Bearer token or X-API-Key for auth endpoints."""
    if x_api_key:
        auth = await get_current_user_from_api_key(x_api_key, db)
        return auth["user_id"]
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")
        try:
            payload = decode_access_token(token)
            return payload["sub"]
        except Exception:
            raise HTTPException(401, detail="Invalid or expired token")
    raise HTTPException(401, detail="Missing authentication")


# ── Google OAuth ──────────────────────────────────────────────────────────────


class GoogleAuthRequest(BaseModel):
    credential: str


@router.post("/google", response_model=TokenResponse)
async def google_auth(body: GoogleAuthRequest, db: AsyncSession = Depends(get_session)):
    """Verify Google ID token and sign in (auto-register if new user)."""
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests

    if not settings.google_client_id:
        raise HTTPException(501, detail="Google OAuth not configured")

    # Verify Google ID token
    try:
        idinfo = id_token.verify_oauth2_token(
            body.credential,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError:
        raise HTTPException(401, detail="Invalid Google credential")

    email = idinfo.get("email")
    email_verified = idinfo.get("email_verified", False)
    if not email or not email_verified:
        raise HTTPException(401, detail="Google account email not verified")

    google_sub = idinfo.get("sub")
    name = idinfo.get("name", "")
    picture = idinfo.get("picture", "")

    # Find or create user
    user = await db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(
            email=email,
            hashed_password="",  # No password for Google users
            google_sub=google_sub,
            display_name=name,
            avatar_url=picture,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # Update Google info on existing user
        if not user.google_sub:
            user.google_sub = google_sub
        if name and not user.display_name:
            user.display_name = name
        if picture:
            user.avatar_url = picture
        await db.commit()

    # Issue tokens
    tokens = AuthService(db)._issue_tokens(user)
    return {**tokens, "token_type": "bearer"}


# ── Auth: Me, Keys ────────────────────────────────────────────────────────────


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: str = Depends(_resolve_user_id_flexible),
    db: AsyncSession = Depends(get_session),
):
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(404, detail="USER_NOT_FOUND")
    return user


@router.get("/keys", response_model=list[ApiKeyListItem])
async def list_keys(
    user_id: str = Depends(_resolve_user_id_flexible),
    db: AsyncSession = Depends(get_session),
):
    return await AuthService(db).list_api_keys(user_id)


@router.post("/keys", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_key(
    body: ApiKeyCreateRequest,
    user_id: str = Depends(_resolve_user_id_flexible),
    db: AsyncSession = Depends(get_session),
):
    scopes = body.scopes if body.scopes else ALL_SCOPES
    return await AuthService(db).create_api_key(user_id, body.name, scopes)


@router.delete("/keys/{key_id}", status_code=204)
async def delete_key(
    key_id: str,
    user_id: str = Depends(_resolve_user_id_flexible),
    db: AsyncSession = Depends(get_session),
):
    await AuthService(db).delete_api_key(user_id, key_id)
    return Response(status_code=204)


# ── Wallet Auth ───────────────────────────────────────────────────────────────


@router.post("/wallet/challenge")
async def wallet_challenge(
    body: dict,
    db: AsyncSession = Depends(get_session),
    redis: aioredis.Redis = Depends(get_redis),
):
    return await AuthService(db).create_wallet_challenge(body["wallet_address"], redis)


@router.post("/wallet/verify", response_model=TokenResponse)
async def wallet_verify(
    body: dict,
    db: AsyncSession = Depends(get_session),
    redis: aioredis.Redis = Depends(get_redis),
):
    tokens = await AuthService(db).verify_wallet_signature(
        body["wallet_address"], body["signature"], redis
    )
    return {**tokens, "token_type": "bearer"}
