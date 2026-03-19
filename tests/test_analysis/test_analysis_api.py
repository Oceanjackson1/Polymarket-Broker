# tests/test_analysis/test_analysis_api.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, UTC, date
from decimal import Decimal
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_analysis_key(test_db_session, email: str) -> str:
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    result = await svc.create_api_key(user.id, "Analysis Key", ["analysis:read"])
    return result["key"], user.id


async def _seed_nba_game(test_db_session, game_id: str):
    from api.data.nba.models import NbaGame
    game = NbaGame(
        game_id=game_id,
        home_team="Los Angeles Lakers",
        away_team="Golden State Warriors",
        game_date=date.today(),
        game_status="live",
        score_home=94, score_away=87,
        quarter=3, time_remaining="4:22",
        home_win_prob=Decimal("0.69"), away_win_prob=Decimal("0.31"),
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(game)
    await test_db_session.commit()


MOCK_AI_MARKET_RESPONSE = '{"probability": 0.72, "reasoning": "Based on current polling data, the probability is higher than market price suggests."}'
MOCK_AI_SCAN_RESPONSE = '[{"market_id": "mkt1", "question": "Test?", "current_price": 0.5, "estimated_prob": 0.7, "reasoning": "Mispriced", "confidence": "high"}]'
MOCK_AI_NBA_RESPONSE = '{"suggestion": "BUY_HOME", "confidence": 0.75, "reasoning": "Lakers leading by 7 in Q3 with strong momentum."}'
MOCK_AI_ASK_RESPONSE = "Polymarket is a prediction market platform where users trade on the outcomes of real-world events."


def _mock_ai():
    mock = MagicMock()
    async def mock_analyze(system_prompt, user_prompt, **kwargs):
        if "prediction market analyst" in system_prompt:
            return MOCK_AI_MARKET_RESPONSE
        elif "scanner" in system_prompt:
            return MOCK_AI_SCAN_RESPONSE
        elif "NBA" in system_prompt:
            return MOCK_AI_NBA_RESPONSE
        return MOCK_AI_ASK_RESPONSE
    mock.analyze = AsyncMock(side_effect=mock_analyze)
    return mock


def _mock_gamma(markets):
    mock = MagicMock()
    mock.get_markets = AsyncMock(return_value=markets)
    mock.close = AsyncMock()
    return mock


async def test_analyze_market(client, test_db_session):
    key, _ = await _create_analysis_key(test_db_session, "analysis_market@example.com")

    mock_markets = [{"id": "mkt_test_001", "question": "Will it rain?", "outcomePrices": ["0.60", "0.40"], "tags": ["weather"]}]

    with patch("api.analysis.router._get_ai_client", return_value=_mock_ai()), \
         patch("core.polymarket.gamma_client.GammaClient", return_value=_mock_gamma(mock_markets)):

        resp = await client.get("/api/v1/analysis/market/mkt_test_001", headers={"X-API-Key": key})

    assert resp.status_code == 200
    data = resp.json()
    assert data["market_id"] == "mkt_test_001"
    assert data["ai_probability"] == 0.72
    assert "reasoning" in data["ai_reasoning"].lower() or len(data["ai_reasoning"]) > 0
    assert data["bias_direction"] in ("AI_HIGHER", "MARKET_HIGHER", "NEUTRAL")


async def test_scan_markets(client, test_db_session):
    key, _ = await _create_analysis_key(test_db_session, "analysis_scan@example.com")

    mock_markets = [
        {"id": f"mkt_{i}", "question": f"Q{i}?", "outcomePrices": ["0.50", "0.50"], "tags": ["politics"]}
        for i in range(5)
    ]

    with patch("api.analysis.router._get_ai_client", return_value=_mock_ai()), \
         patch("core.polymarket.gamma_client.GammaClient", return_value=_mock_gamma(mock_markets)):

        resp = await client.post(
            "/api/v1/analysis/scan",
            json={"category": "politics", "min_bias_bps": 500, "limit": 5},
            headers={"X-API-Key": key},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "opportunities" in data
    assert "scan_duration_ms" in data


async def test_analyze_nba(client, test_db_session):
    key, _ = await _create_analysis_key(test_db_session, "analysis_nba@example.com")
    await _seed_nba_game(test_db_session, "espn_ai_001")

    with patch("api.analysis.router._get_ai_client", return_value=_mock_ai()):
        resp = await client.get("/api/v1/analysis/nba/espn_ai_001", headers={"X-API-Key": key})

    assert resp.status_code == 200
    data = resp.json()
    assert data["game_id"] == "espn_ai_001"
    assert data["ai_suggestion"] in ("BUY_HOME", "BUY_AWAY", "HOLD")
    assert data["home_team"] == "Los Angeles Lakers"


async def test_analyze_nba_not_found(client, test_db_session):
    key, _ = await _create_analysis_key(test_db_session, "analysis_nba404@example.com")

    with patch("api.analysis.router._get_ai_client", return_value=_mock_ai()):
        resp = await client.get("/api/v1/analysis/nba/nonexistent", headers={"X-API-Key": key})

    assert resp.status_code == 404


async def test_ask_question(client, test_db_session):
    key, _ = await _create_analysis_key(test_db_session, "analysis_ask@example.com")

    with patch("api.analysis.router._get_ai_client", return_value=_mock_ai()):
        resp = await client.post(
            "/api/v1/analysis/ask",
            json={"question": "What is Polymarket?"},
            headers={"X-API-Key": key},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["question"] == "What is Polymarket?"
    assert "Polymarket" in data["answer"]


async def test_analysis_requires_scope(client, test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("analysis_noscope@example.com", "password123")
    result = await svc.create_api_key(user.id, "No Scope", ["data:read"])

    resp = await client.get("/api/v1/analysis/market/mkt_001", headers={"X-API-Key": result["key"]})
    assert resp.status_code == 403


async def test_quota_enforcement(client, test_db_session, test_redis):
    key, user_id = await _create_analysis_key(test_db_session, "analysis_quota@example.com")

    # Exhaust quota
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    quota_key = f"analysis_quota:{user_id}:{today}"
    await test_redis.set(quota_key, "10")
    await test_redis.expire(quota_key, 86400)

    with patch("api.analysis.router._get_ai_client", return_value=_mock_ai()):
        resp = await client.post(
            "/api/v1/analysis/ask",
            json={"question": "Test quota"},
            headers={"X-API-Key": key},
        )

    assert resp.status_code == 429
