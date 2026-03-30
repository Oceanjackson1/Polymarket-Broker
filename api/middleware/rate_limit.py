import hashlib
import time
from datetime import datetime, UTC
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse

from db.redis_client import get_redis


DAILY_LIMIT_FREE = 500   # Free tier daily call limit


async def _get_redis(app):
    """Return the Redis client, checking dependency overrides first (for tests)."""
    redis = getattr(app.state, "redis", None)
    if redis is not None:
        return redis
    # Fall back to dependency override (useful in test environments where lifespan doesn't run)
    override = app.dependency_overrides.get(get_redis)
    if override is not None:
        result = override()
        import inspect
        if inspect.isawaitable(result):
            return await result
        return result
    return None


async def _resolve_user_id(redis, api_key_raw: str) -> str | None:
    """Resolve X-API-Key to user_id via key_hash lookup in DB."""
    from sqlalchemy import select
    from api.auth.models import ApiKey
    from db.postgres import AsyncSessionLocal

    key_hash = hashlib.sha256(api_key_raw.encode()).hexdigest()
    async with AsyncSessionLocal() as db:
        row = await db.scalar(
            select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
        )
        return row.user_id if row else None


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from starlette.requests import Request
        request = Request(scope, receive)
        redis = await _get_redis(request.app)

        if redis is None:
            await self.app(scope, receive, send)
            return

        # --- IP-based rate limiting (existing) ---
        ip = request.client.host if request.client else "unknown"
        day_key = f"ratelimit:ip:{ip}:calls"

        calls_today = await redis.incr(day_key)
        if calls_today == 1:
            await redis.expire(day_key, 86400)

        ttl = await redis.ttl(day_key)
        reset_at = int(time.time()) + max(ttl, 0)
        remaining = max(0, DAILY_LIMIT_FREE - calls_today)

        if calls_today > DAILY_LIMIT_FREE:
            response = JSONResponse(
                status_code=429,
                content={"error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Daily API limit reached. Upgrade to Pro for unlimited access.",
                    "details": {}
                }},
                headers={
                    "Retry-After": "3600",
                    "X-RateLimit-Limit": str(DAILY_LIMIT_FREE),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                }
            )
            await response(scope, receive, send)
            return

        # --- Per-user usage tracking (for /developer/usage) ---
        api_key_raw = request.headers.get("x-api-key")
        if api_key_raw:
            try:
                user_id = await _resolve_user_id(redis, api_key_raw)
                if user_id:
                    today = datetime.now(UTC).strftime("%Y-%m-%d")
                    user_key = f"rate_limit:{user_id}:{today}"
                    await redis.incr(user_key)
                    current_ttl = await redis.ttl(user_key)
                    if current_ttl < 0:
                        await redis.expire(user_key, 86400)
            except Exception:
                pass  # Don't block request if tracking fails

        # Intercept send to inject headers into the response
        rl_headers = {
            "X-RateLimit-Limit": str(DAILY_LIMIT_FREE),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_at),
        }

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for key, value in rl_headers.items():
                    headers.append(key, value)
            await send(message)

        await self.app(scope, receive, send_with_headers)
