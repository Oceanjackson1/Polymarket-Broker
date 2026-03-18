# tests/test_orders/test_order_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.orders.service import OrderService
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_place_order_stores_in_db(test_db_session):
    # Create a real user
    auth = AuthService(test_db_session)
    user = await auth.register("ordertest@example.com", "pass123")

    mock_clob_response = {"orderID": "poly_order_001", "status": "live"}

    with patch("api.orders.service.ClobClient") as MockClob:
        mock_instance = MagicMock()
        mock_instance.post_order = AsyncMock(return_value=mock_clob_response)
        MockClob.return_value = mock_instance

        svc = OrderService(test_db_session)
        order = await svc.place_order(
            user_id=user.id,
            tier="free",
            market_id="0xabc",
            token_id="21742633",
            side="BUY",
            order_type="LIMIT",
            price=0.5,
            size=10.0,
        )

    assert order.status == "OPEN"
    assert order.broker_fee_bps == 10  # Free tier
    assert order.polymarket_order_id == "poly_order_001"
    assert order.mode == "hosted"


async def test_place_order_rejects_oversized(test_db_session):
    auth = AuthService(test_db_session)
    user = await auth.register("ordersize@example.com", "pass123")
    svc = OrderService(test_db_session)

    with pytest.raises(ValueError, match="ORDER_SIZE_EXCEEDED"):
        await svc.place_order(
            user_id=user.id,
            tier="free",
            market_id="0xabc",
            token_id="21742633",
            side="BUY",
            order_type="LIMIT",
            price=0.9,
            size=2000.0,  # 1800 USDC > 1000 free tier limit
        )


async def test_list_orders_returns_user_orders(test_db_session):
    auth = AuthService(test_db_session)
    user = await auth.register("orderlist@example.com", "pass123")

    mock_clob_response = {"orderID": "poly_list_001", "status": "live"}
    with patch("api.orders.service.ClobClient") as MockClob:
        mock_instance = MagicMock()
        mock_instance.post_order = AsyncMock(return_value=mock_clob_response)
        MockClob.return_value = mock_instance
        svc = OrderService(test_db_session)
        await svc.place_order(
            user_id=user.id, tier="free", market_id="0xmarket1",
            token_id="tok1", side="BUY", order_type="LIMIT", price=0.5, size=10.0,
        )

    svc = OrderService(test_db_session)
    result = await svc.list_orders(user_id=user.id)
    assert len(result["data"]) == 1
    assert result["data"][0].market_id == "0xmarket1"


async def test_cancel_order(test_db_session):
    auth = AuthService(test_db_session)
    user = await auth.register("ordercancel@example.com", "pass123")

    mock_clob_response = {"orderID": "poly_cancel_001", "status": "live"}
    with patch("api.orders.service.ClobClient") as MockClob:
        mock_instance = MagicMock()
        mock_instance.post_order = AsyncMock(return_value=mock_clob_response)
        mock_instance.cancel_order = AsyncMock(return_value={"status": "cancelled"})
        MockClob.return_value = mock_instance
        svc = OrderService(test_db_session)
        order = await svc.place_order(
            user_id=user.id, tier="free", market_id="0xcancelmarket",
            token_id="tok1", side="BUY", order_type="LIMIT", price=0.5, size=10.0,
        )
        await svc.cancel_order(user_id=user.id, order_id=order.id, api_key="test_key")

    svc = OrderService(test_db_session)
    result = await svc.list_orders(user_id=user.id, status="CANCELLED")
    assert len(result["data"]) == 1


async def test_cancel_order_not_found_raises(test_db_session):
    auth = AuthService(test_db_session)
    user = await auth.register("cancelnotfound@example.com", "pass123")
    svc = OrderService(test_db_session)
    with pytest.raises(KeyError, match="ORDER_NOT_FOUND"):
        await svc.cancel_order(user_id=user.id, order_id="ord_nonexistent", api_key="key")


async def test_cancel_already_cancelled_raises(test_db_session):
    auth = AuthService(test_db_session)
    user = await auth.register("canceltwice@example.com", "pass123")

    mock_clob_response = {"orderID": "poly_twice_001", "status": "live"}
    with patch("api.orders.service.ClobClient") as MockClob:
        mock_instance = MagicMock()
        mock_instance.post_order = AsyncMock(return_value=mock_clob_response)
        mock_instance.cancel_order = AsyncMock(return_value={"status": "cancelled"})
        MockClob.return_value = mock_instance
        svc = OrderService(test_db_session)
        order = await svc.place_order(
            user_id=user.id, tier="free", market_id="0xtwice",
            token_id="tok1", side="BUY", order_type="LIMIT", price=0.5, size=10.0,
        )
        # Cancel once - succeeds
        await svc.cancel_order(user_id=user.id, order_id=order.id, api_key="test_key")

    svc = OrderService(test_db_session)
    with pytest.raises(ValueError, match="ORDER_NOT_CANCELLABLE"):
        await svc.cancel_order(user_id=user.id, order_id=order.id, api_key="test_key")


async def test_cancel_all_open(test_db_session):
    auth = AuthService(test_db_session)
    user = await auth.register("cancelall@example.com", "pass123")

    mock_clob_response = {"orderID": "poly_all_001", "status": "live"}
    with patch("api.orders.service.ClobClient") as MockClob:
        mock_instance = MagicMock()
        mock_instance.post_order = AsyncMock(return_value=mock_clob_response)
        mock_instance.cancel_order = AsyncMock(return_value={"status": "cancelled"})
        MockClob.return_value = mock_instance
        svc = OrderService(test_db_session)
        # Place 2 orders
        await svc.place_order(
            user_id=user.id, tier="free", market_id="0xallmarket1",
            token_id="tok1", side="BUY", order_type="LIMIT", price=0.5, size=5.0,
        )
        await svc.place_order(
            user_id=user.id, tier="free", market_id="0xallmarket2",
            token_id="tok2", side="BUY", order_type="LIMIT", price=0.4, size=5.0,
        )
        # Cancel all
        count = await svc.cancel_all_open(user_id=user.id, api_key="test_key")

    assert count == 2
    svc = OrderService(test_db_session)
    result = await svc.list_orders(user_id=user.id, status="CANCELLED")
    assert len(result["data"]) == 2
