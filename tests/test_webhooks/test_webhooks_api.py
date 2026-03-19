# tests/test_webhooks/test_webhooks_api.py
import pytest
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_webhook_key(test_db_session, email: str, tier: str = "pro") -> str:
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    user.tier = tier
    await test_db_session.commit()
    result = await svc.create_api_key(user.id, "Webhook Key", ["webhooks:write"])
    return result["key"]


async def test_create_webhook(client, test_db_session):
    key = await _create_webhook_key(test_db_session, "wh_create@example.com")
    resp = await client.post(
        "/api/v1/webhooks",
        json={"url": "https://example.com/webhook", "events": ["order.filled"], "secret": "my_secret_123"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["url"] == "https://example.com/webhook"
    assert data["events"] == ["order.filled"]
    assert data["status"] == "active"
    assert data["id"].startswith("wh_")


async def test_list_webhooks(client, test_db_session):
    key = await _create_webhook_key(test_db_session, "wh_list@example.com")
    # Create one first
    await client.post(
        "/api/v1/webhooks",
        json={"url": "https://example.com/hook2", "events": ["market.resolved"], "secret": "s2"},
        headers={"X-API-Key": key},
    )
    resp = await client.get("/api/v1/webhooks", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_delete_webhook(client, test_db_session):
    key = await _create_webhook_key(test_db_session, "wh_delete@example.com")
    create_resp = await client.post(
        "/api/v1/webhooks",
        json={"url": "https://example.com/hook3", "events": ["order.cancelled"], "secret": "s3"},
        headers={"X-API-Key": key},
    )
    wh_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/webhooks/{wh_id}", headers={"X-API-Key": key})
    assert resp.status_code == 204

    # Verify deleted
    list_resp = await client.get("/api/v1/webhooks", headers={"X-API-Key": key})
    ids = [w["id"] for w in list_resp.json()]
    assert wh_id not in ids


async def test_create_webhook_invalid_events(client, test_db_session):
    key = await _create_webhook_key(test_db_session, "wh_invalid@example.com")
    resp = await client.post(
        "/api/v1/webhooks",
        json={"url": "https://example.com/bad", "events": ["invalid.event"], "secret": "s"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 400


async def test_webhooks_require_pro(client, test_db_session):
    key = await _create_webhook_key(test_db_session, "wh_free@example.com", tier="free")
    resp = await client.post(
        "/api/v1/webhooks",
        json={"url": "https://example.com/free", "events": ["order.filled"], "secret": "s"},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 403


async def test_webhook_dispatcher_signs_correctly():
    from api.webhooks.dispatcher import sign_payload
    sig = sign_payload("my_secret", b'{"test": true}')
    assert sig.startswith("sha256=")
    assert len(sig) == 71  # sha256= + 64 hex chars
