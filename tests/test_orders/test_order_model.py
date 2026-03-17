import pytest
from sqlalchemy import text

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_orders_table_exists(test_db_session):
    result = await test_db_session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_name='orders'")
    )
    assert result.scalar() == "orders"


async def test_order_row_roundtrip(test_db_session):
    from api.orders.models import Order
    from api.auth.models import User
    from sqlalchemy import select

    # Create a real user to satisfy the FK constraint
    user = User(
        email="order_test_user@example.com",
        hashed_password="hashed_pw_placeholder",
    )
    test_db_session.add(user)
    await test_db_session.flush()

    order = Order(
        user_id=user.id,
        market_id="0xabc123",
        token_id="21742633",
        side="BUY",
        type="LIMIT",
        price=0.65,
        size=100.0,
        broker_fee_bps=10,
        mode="hosted",
    )
    test_db_session.add(order)
    await test_db_session.flush()
    fetched = await test_db_session.scalar(
        select(Order).where(Order.market_id == "0xabc123")
    )
    assert fetched is not None
    assert fetched.status == "PENDING"
    assert fetched.size_filled == 0.0
    assert fetched.id.startswith("ord_")
