# tests/test_data/test_nba_api.py
import pytest
from datetime import datetime, UTC, timedelta, date
from unittest.mock import AsyncMock, patch
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_data_key(test_db_session, email: str) -> str:
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    result = await svc.create_api_key(user.id, "Data Key", ["data:read"])
    return result["key"]


async def _seed_nba_game(test_db_session, game_id: str, game_status: str = "live", market_id: str | None = "mkt_nba_001") -> None:
    from api.data.nba.models import NbaGame
    game = NbaGame(
        game_id=game_id,
        home_team="Los Angeles Lakers",
        away_team="Golden State Warriors",
        game_date=date.today(),
        game_status=game_status,
        score_home=94,
        score_away=87,
        quarter=3,
        time_remaining="4:22",
        market_id=market_id,
        home_win_prob=0.69,
        away_win_prob=0.31,
        last_trade_price=0.69,
        bias_direction="HOME_UNDERPRICED",
        bias_magnitude_bps=420,
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(game)
    await test_db_session.commit()


async def test_list_nba_games(client, test_db_session):
    key = await _create_data_key(test_db_session, "nba_list@example.com")
    await _seed_nba_game(test_db_session, "espn_list_001")

    resp = await client.get("/api/v1/data/nba/games", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert len(data["data"]) >= 1


async def test_get_nba_game_detail(client, test_db_session):
    key = await _create_data_key(test_db_session, "nba_detail@example.com")
    await _seed_nba_game(test_db_session, "espn_detail_001")

    resp = await client.get("/api/v1/data/nba/games/espn_detail_001", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["game_id"] == "espn_detail_001"
    assert "stale" in data


async def test_get_nba_game_not_found(client, test_db_session):
    key = await _create_data_key(test_db_session, "nba_notfound@example.com")
    resp = await client.get("/api/v1/data/nba/games/nonexistent_game", headers={"X-API-Key": key})
    assert resp.status_code == 404


async def test_get_nba_fusion(client, test_db_session):
    key = await _create_data_key(test_db_session, "nba_fusion@example.com")
    await _seed_nba_game(test_db_session, "espn_fusion_001")

    resp = await client.get("/api/v1/data/nba/games/espn_fusion_001/fusion", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data
    assert "polymarket" in data
    assert "bias_signal" in data
    assert "stale" in data


async def test_get_nba_orderbook_proxy(client, test_db_session):
    key = await _create_data_key(test_db_session, "nba_ob@example.com")
    await _seed_nba_game(test_db_session, "espn_ob_001", market_id="mkt_nba_ob")

    mock_ob = {"bids": [], "asks": []}
    with patch("api.data.nba.router.clob_client") as mock_clob:
        mock_clob.get_orderbook = AsyncMock(return_value=mock_ob)
        resp = await client.get(
            "/api/v1/data/nba/games/espn_ob_001/orderbook?token_id=tok123",
            headers={"X-API-Key": key}
        )
    assert resp.status_code == 200


async def test_get_nba_orderbook_no_market_returns_404(client, test_db_session):
    key = await _create_data_key(test_db_session, "nba_ob_null@example.com")
    await _seed_nba_game(test_db_session, "espn_ob_null_001", market_id=None)

    resp = await client.get(
        "/api/v1/data/nba/games/espn_ob_null_001/orderbook?token_id=tok123",
        headers={"X-API-Key": key}
    )
    assert resp.status_code == 404


async def test_nba_requires_scope(client, test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("nba_noscope@example.com", "password123")
    result = await svc.create_api_key(user.id, "No Scope", ["orders:write"])
    resp = await client.get("/api/v1/data/nba/games", headers={"X-API-Key": result["key"]})
    assert resp.status_code == 403
