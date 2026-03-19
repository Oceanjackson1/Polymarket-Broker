# tests/test_developer/test_developer_api.py
import pytest
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_key(test_db_session, email: str, scopes=None, tier="free"):
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    if tier != "free":
        user.tier = tier
        await test_db_session.commit()
    result = await svc.create_api_key(user.id, "Dev Key", scopes or ["data:read"])
    return result["key"], user.id


async def test_get_usage(client, test_db_session):
    key, _ = await _create_key(test_db_session, "dev_usage@example.com")
    resp = await client.get("/api/v1/developer/usage", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert "calls_today" in data
    assert "tier" in data
    assert data["tier"] == "free"
    assert data["calls_remaining"] is not None


async def test_get_usage_pro_unlimited(client, test_db_session):
    key, _ = await _create_key(test_db_session, "dev_usage_pro@example.com", tier="pro")
    resp = await client.get("/api/v1/developer/usage", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["calls_remaining"] is None  # unlimited


async def test_get_billing(client, test_db_session):
    key, _ = await _create_key(test_db_session, "dev_billing@example.com")
    resp = await client.get("/api/v1/developer/billing", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "free"
    assert data["amount_due_cents"] == 0


async def test_upgrade_tier(client, test_db_session):
    key, _ = await _create_key(test_db_session, "dev_upgrade@example.com")
    resp = await client.post(
        "/api/v1/developer/billing/upgrade",
        json={"tier": "pro"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["previous_tier"] == "free"
    assert data["new_tier"] == "pro"


async def test_upgrade_invalid_tier(client, test_db_session):
    key, _ = await _create_key(test_db_session, "dev_upgrade_bad@example.com")
    resp = await client.post(
        "/api/v1/developer/billing/upgrade",
        json={"tier": "platinum"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 400


async def test_get_webhook_health(client, test_db_session):
    key, _ = await _create_key(test_db_session, "dev_wh_health@example.com")
    resp = await client.get("/api/v1/developer/webhooks", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_risk_reset(client, test_db_session):
    key, _ = await _create_key(test_db_session, "dev_risk@example.com")
    resp = await client.post("/api/v1/developer/risk/reset", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert "circuit_breaker_reset" in data
