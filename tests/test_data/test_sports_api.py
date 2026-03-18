# tests/test_data/test_sports_api.py
import pytest
from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_data_key(test_db_session, email: str) -> str:
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    result = await svc.create_api_key(user.id, "Data Key", ["data:read"])
    return result["key"]


async def _seed_sports_event(test_db_session, market_id: str, sport_slug: str, status: str = "active"):
    from api.data.sports.models import SportsEvent
    event = SportsEvent(
        market_id=market_id,
        sport_slug=sport_slug,
        question=f"Test question for {market_id}",
        outcomes=[{"name": "Yes"}, {"name": "No"}],
        status=status,
        resolution={"winner": "Yes", "settled_at": "2026-03-18T10:00:00Z"} if status == "resolved" else None,
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(event)
    await test_db_session.commit()


async def test_get_categories(client, test_db_session):
    key = await _create_data_key(test_db_session, "sports_cat@example.com")
    await _seed_sports_event(test_db_session, "mkt_cat_001", "nba")
    await _seed_sports_event(test_db_session, "mkt_cat_002", "nfl")

    resp = await client.get("/api/v1/data/sports/categories", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    slugs = [c["slug"] for c in data]
    assert "nba" in slugs
    assert "nfl" in slugs


async def test_get_categories_requires_scope(client, test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("sports_noscope@example.com", "password123")
    result = await svc.create_api_key(user.id, "No Scope Key", ["orders:write"])
    key = result["key"]

    resp = await client.get("/api/v1/data/sports/categories", headers={"X-API-Key": key})
    assert resp.status_code == 403


async def test_get_sport_events(client, test_db_session):
    key = await _create_data_key(test_db_session, "sports_events@example.com")
    await _seed_sports_event(test_db_session, "mkt_events_001", "nba")

    resp = await client.get("/api/v1/data/sports/nba/events", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "pagination" in data
    assert len(data["data"]) >= 1


async def test_get_sport_events_stale(client, test_db_session):
    """Event with old data_updated_at returns stale=True."""
    key = await _create_data_key(test_db_session, "sports_stale@example.com")
    from api.data.sports.models import SportsEvent
    old_event = SportsEvent(
        market_id="mkt_stale_001", sport_slug="epl",
        question="Old match", outcomes=[],
        status="active",
        data_updated_at=datetime.now(UTC) - timedelta(hours=1),
    )
    test_db_session.add(old_event)
    await test_db_session.commit()

    resp = await client.get("/api/v1/data/sports/epl/events", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert resp.json()["stale"] is True


async def test_get_orderbook_proxy(client, test_db_session):
    key = await _create_data_key(test_db_session, "sports_ob@example.com")
    await _seed_sports_event(test_db_session, "mkt_ob_001", "nba")

    mock_ob = {"bids": [], "asks": []}
    with patch("api.data.sports.router.clob_client") as mock_clob:
        mock_clob.get_orderbook = AsyncMock(return_value=mock_ob)
        resp = await client.get(
            "/api/v1/data/sports/nba/events/mkt_ob_001/orderbook?token_id=tok123",
            headers={"X-API-Key": key}
        )
    assert resp.status_code == 200


async def test_get_realized_resolved(client, test_db_session):
    key = await _create_data_key(test_db_session, "sports_resolved@example.com")
    await _seed_sports_event(test_db_session, "mkt_resolved_001", "nba", status="resolved")

    resp = await client.get(
        "/api/v1/data/sports/nba/events/mkt_resolved_001/realized",
        headers={"X-API-Key": key}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["resolution"]["winner"] == "Yes"


async def test_get_realized_not_resolved_returns_404(client, test_db_session):
    key = await _create_data_key(test_db_session, "sports_notresolved@example.com")
    await _seed_sports_event(test_db_session, "mkt_active_001", "nba", status="active")

    resp = await client.get(
        "/api/v1/data/sports/nba/events/mkt_active_001/realized",
        headers={"X-API-Key": key}
    )
    assert resp.status_code == 404
