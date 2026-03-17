import time
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
        # override may be a sync callable returning a coroutine or the client directly
        import inspect
        if inspect.isawaitable(result):
            return await result
        return result
    return None


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
