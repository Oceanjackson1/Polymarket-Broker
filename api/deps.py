from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres import get_session
from core.security import decode_access_token


async def get_current_user_id(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_session),
) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, detail="Invalid authorization header")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_access_token(token)
        return payload["sub"]
    except Exception:
        raise HTTPException(401, detail="Invalid or expired token")
