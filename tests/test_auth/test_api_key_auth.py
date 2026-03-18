import pytest
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_api_key_lookup_succeeds(test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("apikeytest@example.com", "pass123")
    result = await svc.create_api_key(user.id, "Test Key", ["markets:read"])
    raw_key = result["key"]

    # Verify we can resolve the key back to the user
    resolved = await svc.resolve_api_key(raw_key)
    assert resolved is not None
    assert resolved.user_id == user.id
    assert resolved.is_active is True


async def test_api_key_lookup_wrong_key_returns_none(test_db_session):
    svc = AuthService(test_db_session)
    resolved = await svc.resolve_api_key("pm_live_sk_doesnotexist")
    assert resolved is None
