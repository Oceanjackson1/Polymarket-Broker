import redis.asyncio as aioredis
from core.config import get_settings

settings = get_settings()
_pool: aioredis.Redis | None = None


async def get_redis_pool() -> aioredis.Redis:
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _pool


async def get_redis() -> aioredis.Redis:
    return await get_redis_pool()
