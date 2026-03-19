# core/ai/quota.py
"""Redis-backed daily quota for AI analysis endpoints."""
from datetime import datetime, UTC
import redis.asyncio as aioredis


async def check_and_increment_quota(redis: aioredis.Redis, api_key_id: str, daily_limit: int) -> tuple[bool, int]:
    """Check if the API key has quota remaining. Returns (allowed, remaining).
    
    Uses Redis key: analysis_quota:{api_key_id}:{date} with TTL 86400s.
    """
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    key = f"analysis_quota:{api_key_id}:{today}"
    
    count = await redis.get(key)
    current = int(count) if count else 0
    
    if daily_limit > 0 and current >= daily_limit:
        return False, 0
    
    new_count = await redis.incr(key)
    if new_count == 1:
        await redis.expire(key, 86400)
    
    remaining = max(0, daily_limit - new_count)
    return True, remaining
