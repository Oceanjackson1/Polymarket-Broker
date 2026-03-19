# tests/test_data/test_coinglass_collector.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from sqlalchemy import select, func

pytestmark = pytest.mark.asyncio(loop_scope="session")

# --- Mock CoinGlass API responses (based on real API output 2026-03-19) ---

MOCK_FUNDING_RATE = {
    "code": "0",
    "data": [{
        "symbol": "BTC",
        "stablecoin_margin_list": [
            {"exchange": "Binance", "funding_rate_interval": 8, "funding_rate": 0.001225, "next_funding_time": 1773907200000},
            {"exchange": "OKX", "funding_rate_interval": 8, "funding_rate": 0.00141, "next_funding_time": 1773907200000},
            {"exchange": "Bybit", "funding_rate_interval": 8, "funding_rate": 0.003824, "next_funding_time": 1773907200000},
        ]
    }]
}

MOCK_OI = {
    "code": "0",
    "data": [
        {
            "exchange": "All", "symbol": "BTC",
            "open_interest_usd": 48553217755.59,
            "open_interest_change_percent_5m": 0.06,
            "open_interest_change_percent_15m": 0.02,
            "open_interest_change_percent_1h": 0.26,
            "open_interest_change_percent_4h": -0.03,
            "open_interest_change_percent_24h": -4.34,
        },
        {
            "exchange": "Binance", "symbol": "BTC",
            "open_interest_usd": 8440537078.14,
            "open_interest_change_percent_5m": 0.05,
            "open_interest_change_percent_15m": 0.0,
            "open_interest_change_percent_1h": 0.19,
            "open_interest_change_percent_4h": 0.35,
            "open_interest_change_percent_24h": -9.18,
        },
    ]
}

MOCK_LIQUIDATION = {
    "code": "0",
    "data": [{
        "symbol": "BTC",
        "long_liquidation_usd_24h": 141365380.63,
        "short_liquidation_usd_24h": 10937572.35,
        "long_liquidation_usd_4h": 890212.84,
        "short_liquidation_usd_4h": 1767823.50,
        "long_liquidation_usd_1h": 181537.48,
        "short_liquidation_usd_1h": 1615358.07,
    }]
}

MOCK_TAKER = {
    "code": "0",
    "msg": "success",
    "data": {
        "symbol": "BTC",
        "buy_ratio": 53.95,
        "sell_ratio": 46.05,
        "buy_vol_usd": 1243502955.25,
        "sell_vol_usd": 1061309578.47,
    }
}

MOCK_FEAR_GREED = {
    "code": "0",
    "data": {"data_list": [30.0]}
}


def _mock_get(responses: dict):
    """Create an async mock that returns different responses based on URL path."""
    async def mock_get(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        for path_fragment, response_data in responses.items():
            if path_fragment in url:
                resp.json.return_value = response_data
                return resp
        resp.json.return_value = {"code": "0", "data": []}
        return resp
    return mock_get


async def test_coinglass_collector_stores_btc(test_db_session):
    """Collector fetches CoinGlass data and stores a CryptoDerivatives row for BTC."""
    from data_pipeline.coinglass_collector import CoinGlassCollector
    from api.data.crypto.models import CryptoDerivatives

    responses = {
        "funding-rate": MOCK_FUNDING_RATE,
        "open-interest": MOCK_OI,
        "liquidation": MOCK_LIQUIDATION,
        "taker-buy-sell": MOCK_TAKER,
        "fear-greed": MOCK_FEAR_GREED,
    }

    collector = CoinGlassCollector()
    with pytest.MonkeyPatch.context() as mp:
        import data_pipeline.coinglass_collector as mod
        original_init = mod.httpx.AsyncClient.__init__

        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=_mock_get(responses))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        mp.setattr(mod, "httpx", MagicMock())
        mod.httpx.AsyncClient.return_value = mock_client

        await collector.collect(test_db_session)

    result = await test_db_session.scalar(
        select(CryptoDerivatives)
        .where(CryptoDerivatives.symbol == "BTC")
        .order_by(CryptoDerivatives.recorded_at.desc())
    )
    assert result is not None
    assert result.oi_total_usd == Decimal("48553217755.59")
    assert result.taker_buy_ratio == Decimal("53.95")
    assert result.liq_long_1h_usd == Decimal("181537.48")
    assert result.fear_greed_index == 30
    assert result.funding_rate_avg is not None
    assert len(result.funding_rates_json) == 3


async def test_coinglass_collector_graceful_degradation(test_db_session):
    """If funding API fails, other fields still get stored (funding=NULL)."""
    from data_pipeline.coinglass_collector import CoinGlassCollector
    from api.data.crypto.models import CryptoDerivatives

    responses = {
        "open-interest": MOCK_OI,
        "liquidation": MOCK_LIQUIDATION,
        "taker-buy-sell": MOCK_TAKER,
        "fear-greed": MOCK_FEAR_GREED,
    }

    collector = CoinGlassCollector()

    async def mock_get_with_failure(url, **kwargs):
        if "funding-rate" in url:
            raise Exception("CoinGlass funding rate API down")
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        for path_fragment, response_data in responses.items():
            if path_fragment in url:
                resp.json.return_value = response_data
                return resp
        resp.json.return_value = {"code": "0", "data": []}
        return resp

    import data_pipeline.coinglass_collector as mod
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=mock_get_with_failure)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(mod, "httpx", MagicMock())
        mod.httpx.AsyncClient.return_value = mock_client

        await collector.collect(test_db_session)

    result = await test_db_session.scalar(
        select(CryptoDerivatives)
        .where(CryptoDerivatives.symbol == "BTC")
        .order_by(CryptoDerivatives.recorded_at.desc())
    )
    assert result is not None
    assert result.funding_rate_avg is None
    assert result.oi_total_usd == Decimal("48553217755.59")
    assert result.taker_buy_ratio == Decimal("53.95")


async def test_coinglass_collector_multi_symbol(test_db_session):
    """Collector stores one row per symbol (BTC, ETH, SOL)."""
    from data_pipeline.coinglass_collector import CoinGlassCollector
    from api.data.crypto.models import CryptoDerivatives

    before_count = await test_db_session.scalar(
        select(func.count()).select_from(CryptoDerivatives)
    )

    responses = {
        "funding-rate": MOCK_FUNDING_RATE,
        "open-interest": MOCK_OI,
        "liquidation": MOCK_LIQUIDATION,
        "taker-buy-sell": MOCK_TAKER,
        "fear-greed": MOCK_FEAR_GREED,
    }

    collector = CoinGlassCollector()
    import data_pipeline.coinglass_collector as mod
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=_mock_get(responses))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(mod, "httpx", MagicMock())
        mod.httpx.AsyncClient.return_value = mock_client

        await collector.collect(test_db_session)

    after_count = await test_db_session.scalar(
        select(func.count()).select_from(CryptoDerivatives)
    )
    assert after_count - before_count == 3
