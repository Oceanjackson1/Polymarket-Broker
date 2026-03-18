# tests/test_data/test_btc_collector.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select, func

pytestmark = pytest.mark.asyncio(loop_scope="session")

TIMEFRAMES = ["5m", "15m", "1h", "4h"]


async def test_btc_collector_appends_snapshots(test_db_session):
    """Collector appends 4 rows (one per timeframe) on each collect cycle."""
    from data_pipeline.btc_collector import BtcCollector
    from api.data.btc.models import BtcSnapshot

    mock_coingecko = {"bitcoin": {"usd": 67420.50}}
    mock_gamma_markets = [
        {"id": f"btc_mkt_{tf}", "question": f"BTC up {tf}?", "active": True, "outcomePrices": ["0.61", "0.39"]}
        for tf in TIMEFRAMES
    ]

    with patch("data_pipeline.btc_collector.httpx") as mock_httpx, \
         patch("data_pipeline.btc_collector.GammaClient") as MockGamma:

        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_coingecko
        mock_resp.raise_for_status = MagicMock()
        mock_httpx.AsyncClient.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

        inst = MockGamma.return_value
        inst.get_markets = AsyncMock(return_value=mock_gamma_markets)

        collector = BtcCollector()
        await collector.collect(test_db_session)

    count = await test_db_session.scalar(
        select(func.count()).select_from(BtcSnapshot).where(BtcSnapshot.price_usd == 67420.50)
    )
    assert count == 4  # one per timeframe


async def test_btc_collector_appends_on_each_cycle(test_db_session):
    """append-only: two cycles → two rows per timeframe."""
    from data_pipeline.btc_collector import BtcCollector
    from api.data.btc.models import BtcSnapshot
    from sqlalchemy import func

    mock_coingecko = {"bitcoin": {"usd": 68000.00}}
    mock_gamma_markets = [
        {"id": f"btc_append_{tf}", "question": f"BTC {tf}", "active": True, "outcomePrices": ["0.55", "0.45"]}
        for tf in TIMEFRAMES
    ]

    for _ in range(2):
        with patch("data_pipeline.btc_collector.httpx") as mock_httpx, \
             patch("data_pipeline.btc_collector.GammaClient") as MockGamma:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_coingecko
            mock_resp.raise_for_status = MagicMock()
            mock_httpx.AsyncClient.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
            inst = MockGamma.return_value
            inst.get_markets = AsyncMock(return_value=mock_gamma_markets)
            collector = BtcCollector()
            await collector.collect(test_db_session)

    count = await test_db_session.scalar(
        select(func.count()).select_from(BtcSnapshot).where(BtcSnapshot.price_usd == 68000.00)
    )
    assert count == 8  # 4 timeframes × 2 cycles
