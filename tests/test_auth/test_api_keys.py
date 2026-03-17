import pytest
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_create_api_key_returns_full_key(test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("keyowner@example.com", "pass123")
    result = await svc.create_api_key(user.id, "My Bot", ["markets:read", "orders:write"])
    assert result["key"].startswith("pm_live_sk_")
    assert result["name"] == "My Bot"
    assert result["scopes"] == ["markets:read", "orders:write"]


async def test_list_keys_returns_created_key(test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("listkeys@example.com", "pass123")
    await svc.create_api_key(user.id, "Bot1", ["markets:read"])
    keys = await svc.list_api_keys(user.id)
    assert len(keys) == 1
    assert keys[0].name == "Bot1"


async def test_delete_key_deactivates(test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("deletekey@example.com", "pass")
    result = await svc.create_api_key(user.id, "ToDelete", ["markets:read"])
    await svc.delete_api_key(user.id, result["id"])
    keys = await svc.list_api_keys(user.id)
    assert len(keys) == 0
