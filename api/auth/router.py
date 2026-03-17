from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from db.postgres import get_session
from db.redis_client import get_redis
from api.deps import get_current_user_id
from api.auth.service import AuthService
from api.auth.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse,
    ApiKeyCreateRequest, ApiKeyCreatedResponse, ApiKeyListItem,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_session)):
    return await AuthService(db).register(body.email, body.password)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_session)):
    tokens = await AuthService(db).login(body.email, body.password)
    return {**tokens, "token_type": "bearer"}


@router.get("/keys", response_model=list[ApiKeyListItem])
async def list_keys(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    return await AuthService(db).list_api_keys(user_id)


@router.post("/keys", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_key(
    body: ApiKeyCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    return await AuthService(db).create_api_key(user_id, body.name, body.scopes)


@router.delete("/keys/{key_id}", status_code=204)
async def delete_key(
    key_id: str,
    user_id: str = Depends(get_current_user_id),
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
