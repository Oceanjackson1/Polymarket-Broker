# tests/test_portfolio/test_portfolio_service.py
"""Direct tests for PortfolioService business logic."""
import pytest
from decimal import Decimal
from datetime import datetime, UTC
from api.orders.models import Order
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_user_and_seed_orders(db, email: str):
    """Create user then seed orders (FK constraint)."""
    svc = AuthService(db)
    user = await svc.register(email, "password123")
    user_id = user.id

    orders = [
        Order(
            id=f"ord_pf_buy_{email[:6]}", user_id=user_id,
            market_id="mkt_pf_001", token_id="tok_pf_001",
            side="BUY", type="LIMIT",
            price=Decimal("0.50"), size=Decimal("100"),
            size_filled=Decimal("100"), status="FILLED",
            broker_fee_bps=10,
            created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
        ),
        Order(
            id=f"ord_pf_sell_{email[:6]}", user_id=user_id,
            market_id="mkt_pf_001", token_id="tok_pf_001",
            side="SELL", type="LIMIT",
            price=Decimal("0.70"), size=Decimal("50"),
            size_filled=Decimal("50"), status="FILLED",
            broker_fee_bps=10,
            created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
        ),
        Order(
            id=f"ord_pf_open_{email[:6]}", user_id=user_id,
            market_id="mkt_pf_002", token_id="tok_pf_002",
            side="BUY", type="LIMIT",
            price=Decimal("0.60"), size=Decimal("200"),
            size_filled=Decimal("0"), status="OPEN",
            broker_fee_bps=5,
            created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
        ),
    ]
    for o in orders:
        db.add(o)
    await db.commit()
    return user_id


async def test_get_positions_aggregates(test_db_session):
    from api.portfolio.service import PortfolioService
    user_id = await _create_user_and_seed_orders(test_db_session, "pf_pos@example.com")

    svc = PortfolioService(test_db_session)
    positions = await svc.get_positions(user_id)
    assert len(positions) >= 1
    pos = next((p for p in positions if p["token_id"] == "tok_pf_001"), None)
    assert pos is not None
    assert pos["order_count"] == 2
    assert pos["size_held"] == 150.0


async def test_get_pnl_calculates_realized(test_db_session):
    from api.portfolio.service import PortfolioService
    user_id = await _create_user_and_seed_orders(test_db_session, "pf_pnl@example.com")

    svc = PortfolioService(test_db_session)
    pnl = await svc.get_pnl(user_id)
    assert "realized" in pnl
    assert "fees_paid_broker" in pnl
    assert pnl["fees_paid_broker"] == pytest.approx(0.085, abs=0.001)


async def test_get_balance_calculates_locked(test_db_session):
    from api.portfolio.service import PortfolioService
    user_id = await _create_user_and_seed_orders(test_db_session, "pf_bal@example.com")

    svc = PortfolioService(test_db_session)
    balance = await svc.get_balance(user_id)
    assert "locked" in balance
    assert "available" in balance
    assert balance["locked"] == pytest.approx(120.0, abs=0.01)
