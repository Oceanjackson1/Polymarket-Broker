# tests/test_data/test_sports_collector.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_sports_collector_upserts_market(test_db_session):
    """Collector fetches Gamma markets and upserts to sports_events."""
    from data_pipeline.sports_collector import SportsCollector
    from api.data.sports.models import SportsEvent

    mock_markets = [
        {
            "id": "mkt_nba_test_001",
            "question": "Will Lakers win vs Warriors?",
            "active": True,
            "tags": ["sports", "nba"],
            "outcomes": [{"name": "Yes"}, {"name": "No"}],
            "volume": "5000.0",
        }
    ]

    collector = SportsCollector()
    with patch("data_pipeline.sports_collector.GammaClient") as MockGamma:
        inst = MockGamma.return_value
        # First call returns markets, second call returns empty (stop pagination)
        inst.get_markets = AsyncMock(side_effect=[mock_markets, []])
        await collector.collect(test_db_session)

    result = await test_db_session.scalar(
        select(SportsEvent).where(SportsEvent.market_id == "mkt_nba_test_001")
    )
    assert result is not None
    assert result.sport_slug == "nba"
    assert result.question == "Will Lakers win vs Warriors?"
    assert result.status == "active"


async def test_sports_collector_upsert_is_idempotent(test_db_session):
    """Running collect twice doesn't create duplicates."""
    from data_pipeline.sports_collector import SportsCollector
    from api.data.sports.models import SportsEvent
    from sqlalchemy import func, select as sa_select

    mock_markets = [
        {"id": "mkt_nba_test_002", "question": "Q2", "active": True, "tags": ["nba"], "outcomes": []}
    ]

    collector = SportsCollector()
    for _ in range(2):
        with patch("data_pipeline.sports_collector.GammaClient") as MockGamma:
            inst = MockGamma.return_value
            inst.get_markets = AsyncMock(side_effect=[mock_markets, []])
            await collector.collect(test_db_session)

    count = await test_db_session.scalar(
        sa_select(func.count()).where(SportsEvent.market_id == "mkt_nba_test_002")
    )
    assert count == 1


async def test_parse_sport_slug_extracts_from_tags():
    from data_pipeline.sports_collector import _parse_sport_slug
    assert _parse_sport_slug(["sports", "nba"]) == "nba"
    assert _parse_sport_slug(["nfl"]) == "nfl"
    assert _parse_sport_slug(["sports"]) == "sports"
    assert _parse_sport_slug([]) == "sports"
