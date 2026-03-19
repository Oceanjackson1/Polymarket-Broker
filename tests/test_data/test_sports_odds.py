# tests/test_data/test_sports_odds.py
"""Tests for sports odds models, collector, and API endpoints."""
import pytest
from decimal import Decimal
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


# --- Model tests ---

async def test_sports_odds_crud(test_db_session):
    from api.data.sports.odds_models import SportsOdds
    row = SportsOdds(
        sport_key="soccer_epl",
        event_id="evt_odds_001",
        home_team="Arsenal",
        away_team="Chelsea",
        bookmaker_count=15,
        home_odds_avg=Decimal("1.8500"),
        away_odds_avg=Decimal("4.2000"),
        home_implied_prob=Decimal("0.5405"),
        away_implied_prob=Decimal("0.2381"),
        bias_direction="BOOKMAKER_HIGHER",
        bias_bps=500,
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(row)
    await test_db_session.commit()
    await test_db_session.refresh(row)
    assert row.id is not None


async def test_sports_score_crud(test_db_session):
    from api.data.sports.odds_models import SportsScore
    row = SportsScore(
        sport_key="soccer_epl",
        event_id="evt_score_001",
        home_team="Arsenal",
        away_team="Chelsea",
        home_score=2,
        away_score=1,
        completed=True,
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(row)
    await test_db_session.commit()
    assert row.id is not None


# --- Collector logic tests ---

def test_compute_implied_prob():
    from data_pipeline.sports_odds_collector import _compute_implied_prob
    assert abs(_compute_implied_prob(2.0) - 0.5) < 0.01
    assert abs(_compute_implied_prob(1.0) - 1.0) < 0.01
    assert abs(_compute_implied_prob(4.0) - 0.25) < 0.01


def test_compute_bias():
    from data_pipeline.sports_odds_collector import _compute_bias
    d, bps = _compute_bias(0.60, 0.50)
    assert d == "BOOKMAKER_HIGHER"
    assert bps >= 999

    d, bps = _compute_bias(0.50, 0.60)
    assert d == "POLYMARKET_HIGHER"
    assert bps >= 999

    d, bps = _compute_bias(0.50, 0.52)
    assert d == "NEUTRAL"


def test_match_polymarket_event():
    from data_pipeline.sports_odds_collector import _match_polymarket_event

    class FakeEvent:
        def __init__(self, question, market_id):
            self.question = question
            self.market_id = market_id
            self.outcomes = []

    events = [
        FakeEvent("Will Arsenal beat Chelsea?", "mkt_001"),
        FakeEvent("Will Lakers win?", "mkt_002"),
    ]
    match = _match_polymarket_event("Arsenal", "Chelsea", events)
    assert match is not None
    assert match.market_id == "mkt_001"

    no_match = _match_polymarket_event("Barcelona", "Real Madrid", events)
    assert no_match is None


# --- API endpoint tests ---

async def _create_data_key(test_db_session, email: str) -> str:
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    result = await svc.create_api_key(user.id, "Sports Key", ["data:read"])
    return result["key"]


async def _seed_odds(test_db_session):
    from api.data.sports.odds_models import SportsOdds
    row = SportsOdds(
        sport_key="soccer_epl",
        event_id="evt_api_test_001",
        home_team="Manchester United",
        away_team="Liverpool",
        bookmaker_count=20,
        home_odds_avg=Decimal("2.5000"),
        away_odds_avg=Decimal("2.8000"),
        home_implied_prob=Decimal("0.4000"),
        away_implied_prob=Decimal("0.3571"),
        bookmakers_json=[{"bookmaker": "Bet365", "home": 2.5, "away": 2.8}],
        polymarket_market_id="mkt_pm_001",
        polymarket_prob=Decimal("0.3500"),
        bias_direction="BOOKMAKER_HIGHER",
        bias_bps=500,
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(row)
    await test_db_session.commit()


async def test_list_tracked_sports(client, test_db_session):
    key = await _create_data_key(test_db_session, "odds_sports@example.com")
    await _seed_odds(test_db_session)
    resp = await client.get("/api/v1/data/sports-odds/sports", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert any(s["sport_key"] == "soccer_epl" for s in data)


async def test_get_odds_by_sport(client, test_db_session):
    key = await _create_data_key(test_db_session, "odds_list@example.com")
    resp = await client.get("/api/v1/data/sports-odds/odds?sport=soccer_epl", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1


async def test_get_event_odds(client, test_db_session):
    key = await _create_data_key(test_db_session, "odds_detail@example.com")
    resp = await client.get("/api/v1/data/sports-odds/odds/evt_api_test_001", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["home_team"] == "Manchester United"


async def test_get_event_bookmakers(client, test_db_session):
    key = await _create_data_key(test_db_session, "odds_bk@example.com")
    resp = await client.get("/api/v1/data/sports-odds/odds/evt_api_test_001/bookmakers", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["bookmaker_count"] == 20
    assert len(data["bookmakers"]) >= 1


async def test_bias_opportunities(client, test_db_session):
    key = await _create_data_key(test_db_session, "odds_bias@example.com")
    resp = await client.get("/api/v1/data/sports-odds/bias-opportunities?min_bias_bps=300", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert all(d["bias_bps"] >= 300 for d in data)


async def test_odds_requires_scope(client, test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("odds_noscope@example.com", "password123")
    result = await svc.create_api_key(user.id, "No Scope", ["orders:write"])
    resp = await client.get("/api/v1/data/sports-odds/sports", headers={"X-API-Key": result["key"]})
    assert resp.status_code == 403
