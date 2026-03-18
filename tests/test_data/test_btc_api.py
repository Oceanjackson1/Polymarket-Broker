# tests/test_data/test_btc_api.py
import pytest
from decimal import Decimal
from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")

TIMEFRAMES = ["5m", "15m", "1h", "4h"]


async def _create_data_key(test_db_session, email: str) -> str:
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    result = await svc.create_api_key(user.id, "BTC Key", ["data:read"])
    return result["key"]


async def _seed_btc_snapshots(test_db_session, price: float = 67000.0) -> None:
    from api.data.btc.models import BtcSnapshot
    for tf in TIMEFRAMES:
        snap = BtcSnapshot(
            timeframe=tf,
            price_usd=Decimal(str(price)),
            market_id=f"btc_{tf}_mkt",
            prediction_prob=Decimal("0.6100"),
            recorded_at=datetime.now(UTC),
        )
        test_db_session.add(snap)
    await test_db_session.commit()


async def test_get_btc_predictions_all(client, test_db_session):
    key = await _create_data_key(test_db_session, "btc_all@example.com")
    await _seed_btc_snapshots(test_db_session, price=67000.0)

    resp = await client.get("/api/v1/data/btc/predictions", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    returned_timeframes = [item["timeframe"] for item in data]
    for tf in TIMEFRAMES:
        assert tf in returned_timeframes


async def test_get_btc_predictions_by_timeframe(client, test_db_session):
    key = await _create_data_key(test_db_session, "btc_tf@example.com")
    await _seed_btc_snapshots(test_db_session, price=67500.0)

    resp = await client.get("/api/v1/data/btc/predictions/5m", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert "stale" in data
    assert "data" in data
    assert len(data["data"]) >= 1
    assert data["data"][0]["timeframe"] == "5m"


async def test_get_btc_predictions_invalid_timeframe(client, test_db_session):
    key = await _create_data_key(test_db_session, "btc_invalid@example.com")
    resp = await client.get("/api/v1/data/btc/predictions/99m", headers={"X-API-Key": key})
    assert resp.status_code == 400


async def test_get_btc_history(client, test_db_session):
    key = await _create_data_key(test_db_session, "btc_hist@example.com")
    await _seed_btc_snapshots(test_db_session, price=69500.0)

    resp = await client.get(
        "/api/v1/data/btc/history?timeframe=1h&limit=10",
        headers={"X-API-Key": key}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert all(item["timeframe"] == "1h" for item in data["data"])


async def test_get_btc_onchain_proxy(client, test_db_session):
    key = await _create_data_key(test_db_session, "btc_onchain@example.com")
    await _seed_btc_snapshots(test_db_session, price=67000.0)

    mock_trades = [{"price": "0.62", "size": "100"}]
    with patch("api.data.btc.router.clob_client") as mock_clob:
        mock_clob.get_trades = AsyncMock(return_value=mock_trades)
        resp = await client.get("/api/v1/data/btc/onchain", headers={"X-API-Key": key})
    assert resp.status_code == 200


async def test_btc_requires_scope(client, test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("btc_noscope@example.com", "password123")
    result = await svc.create_api_key(user.id, "No Scope", ["orders:write"])
    resp = await client.get("/api/v1/data/btc/predictions", headers={"X-API-Key": result["key"]})
    assert resp.status_code == 403
