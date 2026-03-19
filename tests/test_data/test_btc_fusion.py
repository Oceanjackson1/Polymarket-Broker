# tests/test_data/test_btc_fusion.py
import pytest
from decimal import Decimal
from datetime import datetime, UTC
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_data_key(test_db_session, email: str) -> str:
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    result = await svc.create_api_key(user.id, "Fusion Key", ["data:read"])
    return result["key"]


async def _seed_fusion_data(test_db_session):
    """Seed both btc_snapshots and crypto_derivatives with close timestamps."""
    from api.data.btc.models import BtcSnapshot
    from api.data.crypto.models import CryptoDerivatives

    now = datetime.now(UTC)

    snap = BtcSnapshot(
        timeframe="5m",
        price_usd=Decimal("67420.50"),
        market_id="btc_fusion_mkt",
        prediction_prob=Decimal("0.6100"),
        volume=Decimal("5000.00"),
        recorded_at=now,
    )
    test_db_session.add(snap)

    deriv = CryptoDerivatives(
        symbol="BTC",
        funding_rate_avg=Decimal("0.00120000"),
        oi_total_usd=Decimal("48553217755.59"),
        oi_change_pct_1h=Decimal("0.2600"),
        oi_change_pct_4h=Decimal("-0.0300"),
        taker_buy_ratio=Decimal("53.9500"),
        taker_sell_ratio=Decimal("46.0500"),
        liq_long_1h_usd=Decimal("181537.48"),
        liq_short_1h_usd=Decimal("1615358.07"),
        fear_greed_index=30,
        recorded_at=now,
    )
    test_db_session.add(deriv)
    await test_db_session.commit()


async def test_btc_fusion_returns_combined_view(client, test_db_session):
    key = await _create_data_key(test_db_session, "fusion_combo@example.com")
    await _seed_fusion_data(test_db_session)

    resp = await client.get("/api/v1/data/btc/fusion/5m", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["timeframe"] == "5m"
    assert "polymarket" in data
    assert data["polymarket"]["up_prob"] is not None
    assert "spot" in data
    assert "derivatives" in data
    assert data["derivatives"]["funding_rate_avg"] is not None
    assert data["derivatives"]["oi_total_usd"] is not None
    assert data["derivatives"]["taker_buy_ratio"] is not None
    assert "stale" in data


async def test_btc_fusion_invalid_timeframe(client, test_db_session):
    key = await _create_data_key(test_db_session, "fusion_bad_tf@example.com")
    resp = await client.get("/api/v1/data/btc/fusion/99m", headers={"X-API-Key": key})
    assert resp.status_code == 400


async def test_btc_fusion_requires_scope(client, test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("fusion_noscope@example.com", "password123")
    result = await svc.create_api_key(user.id, "No Scope", ["orders:write"])
    resp = await client.get("/api/v1/data/btc/fusion/5m", headers={"X-API-Key": result["key"]})
    assert resp.status_code == 403
