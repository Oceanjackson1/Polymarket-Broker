class _MockRedis:
    """Stub redis pool with aclose method."""

    async def aclose(self) -> None:
        pass


async def get_redis_pool() -> _MockRedis:
    """Stub: Return a Redis connection pool."""
    return _MockRedis()
