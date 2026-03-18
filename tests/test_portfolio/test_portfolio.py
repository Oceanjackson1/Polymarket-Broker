import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.auth.service import AuthService
from api.orders.service import OrderService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _setup_user_with_order(test_db_session, email: str):
    auth = AuthService(test_db_session)
    user = await auth.register(email, "pass123")
    key_result = await auth.create_api_key(user.id, "Key", ["portfolio:read"])
    mock_clob_resp = {"orderID": "poly_port_001", "status": "live"}
    with patch("api.orders.service.ClobClient") as MockClob:
        inst = MagicMock()
        inst.post_order = AsyncMock(return_value=mock_clob_resp)
        MockClob.return_value = inst
        svc = OrderService(test_db_session)
        order = await svc.place_order(
            user_id=user.id, tier="free", market_id="0xportmkt",
            token_id="tok1", side="BUY", order_type="LIMIT", price=0.65, size=50.0,
        )
        # Mark partially filled
        order.status = "PARTIALLY_FILLED"
        order.size_filled = 25.0
        await test_db_session.commit()
    return user, key_result["key"]


async def test_get_positions(client, test_db_session):
    user, api_key = await _setup_user_with_order(test_db_session, "portfolio_pos@example.com")
    resp = await client.get("/api/v1/portfolio/positions", headers={"X-API-Key": api_key})
    assert resp.status_code == 200
    data = resp.json()
    assert "positions" in data
    assert len(data["positions"]) == 1
    assert data["positions"][0]["market_id"] == "0xportmkt"


async def test_get_pnl(client, test_db_session):
    user, api_key = await _setup_user_with_order(test_db_session, "portfolio_pnl@example.com")
    resp = await client.get("/api/v1/portfolio/pnl", headers={"X-API-Key": api_key})
    assert resp.status_code == 200
    data = resp.json()
    assert "realized" in data
    assert "unrealized" in data
    assert "fees_paid_broker" in data


async def test_get_balance(client, test_db_session):
    user, api_key = await _setup_user_with_order(test_db_session, "portfolio_bal@example.com")
    with patch("api.portfolio.service.ClobClient") as MockClob:
        inst = MagicMock()
        inst._get = AsyncMock(return_value={"balance": "1000.00"})
        MockClob.return_value = inst
        resp = await client.get("/api/v1/portfolio/balance", headers={"X-API-Key": api_key})
    assert resp.status_code == 200
    data = resp.json()
    assert "balance" in data
