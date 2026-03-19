# tests/test_strategies/test_strategies_api.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, UTC, timedelta
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_strategy_key(test_db_session, email: str, tier: str = "pro") -> str:
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    # Manually set tier (normally managed by billing)
    user.tier = tier
    await test_db_session.commit()
    result = await svc.create_api_key(user.id, "Strategy Key", ["strategies:execute"])
    return result["key"]


async def test_list_strategies(client, test_db_session):
    key = await _create_strategy_key(test_db_session, "strat_list@example.com")
    resp = await client.get("/api/v1/strategies", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["slug"] == "convergence"


async def test_convergence_opportunities(client, test_db_session):
    key = await _create_strategy_key(test_db_session, "strat_opp@example.com")

    mock_markets = [
        {
            "id": "mkt_conv_001",
            "question": "Will X happen?",
            "outcomePrices": ["0.97", "0.03"],
            "endDate": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            "volume": "10000",
            "active": True,
        },
        {
            "id": "mkt_conv_002",
            "question": "Will Y happen?",
            "outcomePrices": ["0.50", "0.50"],
            "endDate": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            "volume": "5000",
            "active": True,
        },
    ]

    with patch("api.strategies.router.GammaClient") as MockGamma:
        inst = MockGamma.return_value
        inst.get_markets = AsyncMock(return_value=mock_markets)
        inst.close = AsyncMock()
        resp = await client.get("/api/v1/strategies/convergence/opportunities", headers={"X-API-Key": key})

    assert resp.status_code == 200
    data = resp.json()
    # Only mkt_conv_001 qualifies (price >= 0.95)
    assert len(data) >= 1
    assert all(float(o["current_price"]) >= 0.95 for o in data)


async def test_convergence_requires_pro(client, test_db_session):
    key = await _create_strategy_key(test_db_session, "strat_free@example.com", tier="free")
    resp = await client.get("/api/v1/strategies/convergence/opportunities", headers={"X-API-Key": key})
    assert resp.status_code == 403


async def test_strategies_requires_scope(client, test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("strat_noscope@example.com", "password123")
    result = await svc.create_api_key(user.id, "No Scope", ["data:read"])
    resp = await client.get("/api/v1/strategies", headers={"X-API-Key": result["key"]})
    assert resp.status_code == 403
