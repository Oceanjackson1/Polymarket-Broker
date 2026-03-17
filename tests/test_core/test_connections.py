import pytest
from sqlalchemy import text

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_postgres_connection(test_db_session):
    result = await test_db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


async def test_redis_connection(test_redis):
    await test_redis.set("ping", "pong", ex=5)
    val = await test_redis.get("ping")
    assert val == "pong"
