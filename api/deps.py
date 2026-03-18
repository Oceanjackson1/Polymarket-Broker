from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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


async def get_current_user_from_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """
    Resolves X-API-Key header → { user_id, tier, scopes }.
    Raises HTTP 401 if key not found or inactive.
    """
    from api.auth.service import AuthService
    api_key_row = await AuthService(db).resolve_api_key(x_api_key)
    if api_key_row is None:
        raise HTTPException(401, detail="Invalid or inactive API key")
    from api.auth.models import User
    user = await db.scalar(select(User).where(User.id == api_key_row.user_id))
    if user is None or not user.is_active:
        raise HTTPException(401, detail="User account inactive")
    return {"user_id": user.id, "tier": user.tier, "scopes": api_key_row.scopes}


def require_scope(auth: dict, scope: str) -> None:
    """Raise HTTP 403 if the required scope is not present in auth['scopes']."""
    if scope not in auth.get("scopes", []):
        raise HTTPException(403, detail=f"SCOPE_REQUIRED: {scope}")
