from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from typing import Optional

from db.postgres import get_session
from db.redis_client import get_redis
from api.deps import get_current_user_id, get_current_user_from_api_key
from api.auth.service import AuthService
from api.auth.models import User
from api.auth.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse,
    ApiKeyCreateRequest, ApiKeyCreatedResponse, ApiKeyListItem,
)
from core.security import decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


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


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_session)):
    return await AuthService(db).register(body.email, body.password)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_session)):
    tokens = await AuthService(db).login(body.email, body.password)
    return {**tokens, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: str = Depends(_resolve_user_id_flexible),
    db: AsyncSession = Depends(get_session),
):
    from sqlalchemy import select
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
