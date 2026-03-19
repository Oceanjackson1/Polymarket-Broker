"""Tests for Dome data models (MarketSnapshot, CrossPlatformSpread, WalletSnapshot)."""

import pytest
import pytest_asyncio
from datetime import datetime, UTC
from decimal import Decimal
from sqlalchemy import select

from api.data.dome.models import MarketSnapshot, CrossPlatformSpread, WalletSnapshot

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_market_snapshot_create(test_db_session):
    snap = MarketSnapshot(
        market_slug="will-trump-win",
        condition_id="cond123",
        token_id="tok456",
        price=Decimal("0.650000"),
        volume_24h=Decimal("50000.00"),
        open=Decimal("0.600000"),
        high=Decimal("0.700000"),
        low=Decimal("0.580000"),
        close=Decimal("0.650000"),
        recorded_at=datetime.now(UTC),
    )
    test_db_session.add(snap)
    await test_db_session.commit()
    await test_db_session.refresh(snap)
    assert snap.id is not None
    assert snap.market_slug == "will-trump-win"
    assert snap.price == Decimal("0.650000")


async def test_cross_platform_spread_create(test_db_session):
    spread = CrossPlatformSpread(
        polymarket_slug="nba-lakers-celtics",
        kalshi_ticker="NBA-LAL-BOS",
        sport="nba",
        poly_price=Decimal("0.550000"),
        kalshi_price=Decimal("0.580000"),
        spread_bps=300,
        direction="POLY_CHEAP",
        recorded_at=datetime.now(UTC),
    )
    test_db_session.add(spread)
    await test_db_session.commit()
    await test_db_session.refresh(spread)
    assert spread.id is not None
    assert spread.spread_bps == 300
    assert spread.direction == "POLY_CHEAP"


async def test_wallet_snapshot_create(test_db_session):
    snap = WalletSnapshot(
        wallet_address="0xabc123",
        total_pnl=Decimal("1234.560000"),
        position_count=5,
        positions_json=[{"token_id": "tok1", "size": 100}],
        recorded_at=datetime.now(UTC),
    )
    test_db_session.add(snap)
    await test_db_session.commit()
    await test_db_session.refresh(snap)
    assert snap.id is not None
    assert snap.position_count == 5
    assert snap.positions_json[0]["token_id"] == "tok1"
