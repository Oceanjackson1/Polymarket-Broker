# tests/test_data/test_crypto_api.py
import pytest
from decimal import Decimal
from datetime import datetime, UTC
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_data_key(test_db_session, email: str) -> str:
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    result = await svc.create_api_key(user.id, "Crypto Key", ["data:read"])
    return result["key"]


async def _seed_crypto_row(test_db_session, symbol: str = "BTC"):
    from api.data.crypto.models import CryptoDerivatives
    row = CryptoDerivatives(
        symbol=symbol,
        funding_rate_avg=Decimal("0.00120000"),
        funding_rate_max=Decimal("0.01000000"),
        funding_rate_min=Decimal("-0.00075000"),
        funding_rates_json=[
            {"exchange": "Binance", "rate": 0.001225, "interval": 8},
            {"exchange": "OKX", "rate": 0.00141, "interval": 8},
        ],
        next_funding_time=1773907200000,
        oi_total_usd=Decimal("48553217755.59"),
        oi_change_pct_5m=Decimal("0.0600"),
        oi_change_pct_1h=Decimal("0.2600"),
        oi_change_pct_4h=Decimal("-0.0300"),
        oi_change_pct_24h=Decimal("-4.3400"),
        oi_exchanges_json=[{"exchange": "Binance", "oi_usd": 8440537078.14}],
        liq_long_1h_usd=Decimal("181537.48"),
        liq_short_1h_usd=Decimal("1615358.07"),
        liq_long_4h_usd=Decimal("890212.84"),
        liq_short_4h_usd=Decimal("1767823.50"),
        liq_long_24h_usd=Decimal("141365380.63"),
        liq_short_24h_usd=Decimal("10937572.35"),
        taker_buy_ratio=Decimal("53.9500"),
        taker_sell_ratio=Decimal("46.0500"),
        taker_buy_vol_usd=Decimal("1243502955.25"),
        taker_sell_vol_usd=Decimal("1061309578.47"),
        fear_greed_index=30,
        recorded_at=datetime.now(UTC),
    )
    test_db_session.add(row)
    await test_db_session.commit()


async def test_get_funding_rates(client, test_db_session):
    key = await _create_data_key(test_db_session, "crypto_funding@example.com")
    await _seed_crypto_row(test_db_session)
    resp = await client.get("/api/v1/data/crypto/funding-rates?symbol=BTC", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC"
    assert "aggregated" in data
    assert "exchanges" in data


async def test_get_funding_rates_history(client, test_db_session):
    key = await _create_data_key(test_db_session, "crypto_fhist@example.com")
    resp = await client.get("/api/v1/data/crypto/funding-rates/history?symbol=BTC&limit=5", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert "data" in resp.json()


async def test_get_open_interest(client, test_db_session):
    key = await _create_data_key(test_db_session, "crypto_oi@example.com")
    resp = await client.get("/api/v1/data/crypto/open-interest?symbol=BTC", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC"
    assert "total_usd" in data
    assert "changes" in data


async def test_get_open_interest_history(client, test_db_session):
    key = await _create_data_key(test_db_session, "crypto_oihist@example.com")
    resp = await client.get("/api/v1/data/crypto/open-interest/history?symbol=BTC&limit=5", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert "data" in resp.json()


async def test_get_liquidations(client, test_db_session):
    key = await _create_data_key(test_db_session, "crypto_liq@example.com")
    resp = await client.get("/api/v1/data/crypto/liquidations?symbol=BTC", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert "windows" in data
    assert "1h" in data["windows"]


async def test_get_taker_volume(client, test_db_session):
    key = await _create_data_key(test_db_session, "crypto_taker@example.com")
    resp = await client.get("/api/v1/data/crypto/taker-volume?symbol=BTC", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert "buy_ratio" in data


async def test_get_sentiment(client, test_db_session):
    key = await _create_data_key(test_db_session, "crypto_sent@example.com")
    resp = await client.get("/api/v1/data/crypto/sentiment", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert "fear_greed" in data


async def test_get_overview(client, test_db_session):
    key = await _create_data_key(test_db_session, "crypto_overview@example.com")
    resp = await client.get("/api/v1/data/crypto/overview?symbol=BTC", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC"
    assert "funding" in data
    assert "open_interest" in data
    assert "liquidations" in data
    assert "taker_volume" in data


async def test_crypto_requires_scope(client, test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("crypto_noscope@example.com", "password123")
    result = await svc.create_api_key(user.id, "No Scope", ["orders:write"])
    resp = await client.get("/api/v1/data/crypto/funding-rates?symbol=BTC", headers={"X-API-Key": result["key"]})
    assert resp.status_code == 403
