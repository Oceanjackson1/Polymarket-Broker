# tests/test_data/test_data_models.py
import pytest
from decimal import Decimal
from datetime import datetime, UTC, date
from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_sports_event_crud(test_db_session):
    from api.data.sports.models import SportsEvent
    event = SportsEvent(
        market_id="mkt_sports_001",
        sport_slug="nba",
        question="Will Lakers win?",
        outcomes=[{"name": "Yes", "price": 0.72}],
        status="active",
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(event)
    await test_db_session.commit()
    await test_db_session.refresh(event)
    assert event.id is not None
    result = await test_db_session.scalar(
        select(SportsEvent).where(SportsEvent.market_id == "mkt_sports_001")
    )
    assert result.sport_slug == "nba"


async def test_nba_game_crud(test_db_session):
    from api.data.nba.models import NbaGame
    game = NbaGame(
        game_id="espn_game_001",
        home_team="Los Angeles Lakers",
        away_team="Golden State Warriors",
        game_date=date(2026, 3, 18),
        game_status="live",
        score_home=87,
        score_away=94,
        quarter=3,
        time_remaining="4:22",
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(game)
    await test_db_session.commit()
    await test_db_session.refresh(game)
    assert game.id is not None
    result = await test_db_session.scalar(
        select(NbaGame).where(NbaGame.game_id == "espn_game_001")
    )
    assert result.home_team == "Los Angeles Lakers"


async def test_btc_snapshot_crud(test_db_session):
    from api.data.btc.models import BtcSnapshot
    snap = BtcSnapshot(
        timeframe="5m",
        price_usd=Decimal("67420.50"),
        market_id="btc_mkt_001",
        prediction_prob=Decimal("0.6100"),
        recorded_at=datetime.now(UTC),
    )
    test_db_session.add(snap)
    await test_db_session.commit()
    await test_db_session.refresh(snap)
    assert snap.id is not None
    result = await test_db_session.scalar(
        select(BtcSnapshot).where(BtcSnapshot.timeframe == "5m")
    )
    assert result.price_usd == Decimal("67420.50")
