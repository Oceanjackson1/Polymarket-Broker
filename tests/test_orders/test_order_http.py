import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_user_and_api_key(client, test_db_session, email: str) -> tuple[str, str]:
    """Helper: register user, create API key, return (user_id, raw_api_key)."""
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    result = await svc.create_api_key(user.id, "Test Key", ["orders:write"])
    return user.id, result["key"]


async def test_post_order_hosted_returns_order(client, test_db_session):
    user_id, api_key = await _create_user_and_api_key(client, test_db_session, "http_order@example.com")

    mock_clob_resp = {"orderID": "poly_http_001", "status": "live"}
    with patch("api.orders.service.ClobClient") as MockClob:
        inst = MagicMock()
        inst.post_order = AsyncMock(return_value=mock_clob_resp)
        MockClob.return_value = inst
        resp = await client.post("/api/v1/orders", json={
            "market_id": "0xabc", "token_id": "21742633",
            "side": "BUY", "type": "LIMIT", "price": 0.5, "size": 10.0,
        }, headers={"X-API-Key": api_key})

    assert resp.status_code == 201
    data = resp.json()
    assert data["order_id"].startswith("ord_")
    assert data["broker_fee_bps"] == 10  # Free tier
    assert data["mode"] == "hosted"


async def test_get_orders_list(client, test_db_session):
    user_id, api_key = await _create_user_and_api_key(client, test_db_session, "http_list@example.com")

    mock_clob_resp = {"orderID": "poly_list_http_001", "status": "live"}
    with patch("api.orders.service.ClobClient") as MockClob:
        inst = MagicMock()
        inst.post_order = AsyncMock(return_value=mock_clob_resp)
        MockClob.return_value = inst
        await client.post("/api/v1/orders", json={
            "market_id": "0xlist1", "token_id": "tok1",
            "side": "BUY", "type": "LIMIT", "price": 0.5, "size": 5.0,
        }, headers={"X-API-Key": api_key})

    resp = await client.get("/api/v1/orders", headers={"X-API-Key": api_key})
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert len(data["data"]) >= 1


async def test_build_order_route_requires_bearer(client):
    # build endpoint needs Authorization: Bearer (non-custodial = wallet auth)
    resp = await client.post("/api/v1/orders/build", json={
        "market_id": "0xabc", "token_id": "tok", "side": "BUY", "price": 0.5, "size": 10.0,
    })
    assert resp.status_code == 422  # Missing Authorization header


async def test_cancel_order_http(client, test_db_session):
    user_id, api_key = await _create_user_and_api_key(client, test_db_session, "http_cancel@example.com")

    mock_clob_resp = {"orderID": "poly_cancel_http_001", "status": "live"}
    with patch("api.orders.service.ClobClient") as MockClob:
        inst = MagicMock()
        inst.post_order = AsyncMock(return_value=mock_clob_resp)
        inst.cancel_order = AsyncMock(return_value={"status": "cancelled"})
        MockClob.return_value = inst

        place_resp = await client.post("/api/v1/orders", json={
            "market_id": "0xcancel1", "token_id": "tok1",
            "side": "BUY", "type": "LIMIT", "price": 0.5, "size": 5.0,
        }, headers={"X-API-Key": api_key})
        order_id = place_resp.json()["order_id"]

        del_resp = await client.delete(f"/api/v1/orders/{order_id}", headers={"X-API-Key": api_key})

    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "CANCELLED"
