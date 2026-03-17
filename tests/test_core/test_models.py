import pytest
from sqlalchemy import text

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_users_table_exists(test_db_session):
    result = await test_db_session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_name='users'")
    )
    assert result.scalar() == "users"


async def test_api_keys_table_exists(test_db_session):
    result = await test_db_session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_name='api_keys'")
    )
    assert result.scalar() == "api_keys"


async def test_refresh_tokens_table_exists(test_db_session):
    result = await test_db_session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_name='refresh_tokens'")
    )
    assert result.scalar() == "refresh_tokens"


async def test_user_row_roundtrip(test_db_session):
    from api.auth.models import User
    from sqlalchemy import select
    user = User(email="model_test@test.com", hashed_password="hashed")
    test_db_session.add(user)
    await test_db_session.flush()
    fetched = await test_db_session.scalar(select(User).where(User.email == "model_test@test.com"))
    assert fetched is not None
    assert fetched.tier == "free"
    assert fetched.is_active is True
