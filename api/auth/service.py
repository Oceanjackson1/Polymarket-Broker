from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import bcrypt

from api.auth.models import User, ApiKey, RefreshToken
from core.security import (
    encrypt_api_key,
    create_access_token, create_refresh_token,
    decode_refresh_token,
    generate_api_key_value,
)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, email: str, password: str) -> User:
        existing = await self.db.scalar(select(User).where(User.email == email))
        if existing:
            raise ValueError("EMAIL_ALREADY_EXISTS")
        user = User(email=email, hashed_password=_hash_password(password))
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login(self, email: str, password: str) -> dict:
        user = await self.db.scalar(select(User).where(User.email == email))
        if not user or not _verify_password(password, user.hashed_password):
            raise PermissionError("INVALID_CREDENTIALS")
        access = create_access_token({"sub": user.id, "tier": user.tier})
        refresh = create_refresh_token(user.id)
        refresh_payload = decode_refresh_token(refresh)
        rt = RefreshToken(
            jti=refresh_payload["jti"],
            user_id=user.id,
            expires_at=datetime.fromtimestamp(refresh_payload["exp"], UTC),
        )
        self.db.add(rt)
        await self.db.commit()
        return {"access_token": access, "refresh_token": refresh}

    async def create_api_key(self, user_id: str, name: str, scopes: list[str]) -> dict:
        raw_key = generate_api_key_value("pm_live_sk")
        key = ApiKey(
            user_id=user_id,
            name=name,
            key_prefix="pm_live_sk",
            key_encrypted=encrypt_api_key(raw_key),
            key_hint=raw_key[-4:],
            scopes=scopes,
        )
        self.db.add(key)
        await self.db.commit()
        await self.db.refresh(key)
        return {**{c.name: getattr(key, c.name) for c in key.__table__.columns}, "key": raw_key}

    async def list_api_keys(self, user_id: str) -> list[ApiKey]:
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.user_id == user_id, ApiKey.is_active == True)
        )
        return list(result.scalars().all())

    async def delete_api_key(self, user_id: str, key_id: str) -> None:
        key = await self.db.scalar(
            select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
        )
        if not key:
            raise KeyError("API_KEY_NOT_FOUND")
        key.is_active = False
        await self.db.commit()
