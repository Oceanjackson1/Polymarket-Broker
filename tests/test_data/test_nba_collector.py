# tests/test_data/test_nba_collector.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_nba_collector_upserts_game(test_db_session):
    """Collector fetches ESPN scoreboard + Polymarket NBA markets and upserts nba_games."""
    from data_pipeline.nba_collector import NbaCollector
    from api.data.nba.models import NbaGame

    mock_espn_response = {
        "events": [{
            "id": "espn_test_nba_001",
            "competitions": [{
                "competitors": [
                    {"homeAway": "home", "team": {"displayName": "Los Angeles Lakers"}, "score": "94"},
                    {"homeAway": "away", "team": {"displayName": "Golden State Warriors"}, "score": "87"},
                ],
                "status": {
                    "type": {"state": "in", "description": "In Progress"},
                    "displayClock": "4:22",
                    "period": 3,
                }
            }]
        }]
    }
    mock_gamma_markets = [
        {"id": "mkt_nba_lal_gsw", "question": "Will Lakers beat Warriors?",
         "active": True, "outcomePrices": ["0.69", "0.31"]}
    ]

    with patch("data_pipeline.nba_collector.httpx") as mock_httpx, \
         patch("data_pipeline.nba_collector.GammaClient") as MockGamma:

        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_espn_response
        mock_resp.raise_for_status = MagicMock()
        mock_httpx.AsyncClient.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

        inst = MockGamma.return_value
        inst.get_markets = AsyncMock(return_value=mock_gamma_markets)

        collector = NbaCollector()
        await collector.collect(test_db_session)

    result = await test_db_session.scalar(
        select(NbaGame).where(NbaGame.game_id == "espn_test_nba_001")
    )
    assert result is not None
    assert result.home_team == "Los Angeles Lakers"
    assert result.score_home == 94
    assert result.score_away == 87
    assert result.quarter == 3


def test_estimate_win_prob_neutral_at_start():
    from data_pipeline.nba_collector import estimate_win_prob
    # Tied at 0-0 in Q1 → 0.5
    prob = estimate_win_prob(0, 0, 1, "12:00")
    assert abs(prob - 0.5) < 0.01


def test_estimate_win_prob_increases_with_lead():
    from data_pipeline.nba_collector import estimate_win_prob
    # Home leads by 20 in Q4 with 1 min left → high prob
    prob = estimate_win_prob(80, 60, 4, "1:00")
    assert prob > 0.85


def test_compute_bias_home_underpriced():
    from data_pipeline.nba_collector import compute_bias
    direction, bps = compute_bias(0.75, 0.55)
    assert direction == "HOME_UNDERPRICED"
    assert bps == 2000


def test_compute_bias_neutral_when_small_delta():
    from data_pipeline.nba_collector import compute_bias
    direction, bps = compute_bias(0.52, 0.51)
    assert direction == "NEUTRAL"


def test_compute_bias_none_prob():
    from data_pipeline.nba_collector import compute_bias
    direction, bps = compute_bias(None, 0.6)
    assert direction == "NEUTRAL"
    assert bps == 0
