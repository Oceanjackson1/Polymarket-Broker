# tests/test_data/test_crypto_models.py
import pytest
from decimal import Decimal
from datetime import datetime, UTC

from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_crypto_derivatives_crud(test_db_session):
    from api.data.crypto.models import CryptoDerivatives

    row = CryptoDerivatives(
        symbol="BTC",
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
        oi_change_pct_15m=Decimal("0.0200"),
        oi_change_pct_1h=Decimal("0.2600"),
        oi_change_pct_4h=Decimal("-0.0300"),
        oi_change_pct_24h=Decimal("-4.3400"),
        oi_exchanges_json=[
            {"exchange": "CME", "oi_usd": 8657410547.99},
            {"exchange": "Binance", "oi_usd": 8440537078.14},
        ],
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
    await test_db_session.refresh(row)
    assert row.id is not None
    result = await test_db_session.scalar(
        select(CryptoDerivatives).where(
            CryptoDerivatives.symbol == "BTC",
            CryptoDerivatives.id == row.id,
        )
    )
    assert result.oi_total_usd == Decimal("48553217755.59")
    assert result.taker_buy_ratio == Decimal("53.9500")
    assert len(result.funding_rates_json) == 2


async def test_crypto_derivatives_multi_symbol(test_db_session):
    from api.data.crypto.models import CryptoDerivatives
    from sqlalchemy import func

    # Use unique symbols to avoid pollution from other session-scoped tests
    for sym in ["AVAX", "DOGE"]:
        row = CryptoDerivatives(
            symbol=sym,
            oi_total_usd=Decimal("1000000.00"),
            taker_buy_ratio=Decimal("50.0000"),
            taker_sell_ratio=Decimal("50.0000"),
            recorded_at=datetime.now(UTC),
        )
        test_db_session.add(row)
    await test_db_session.commit()

    count = await test_db_session.scalar(
        select(func.count()).select_from(CryptoDerivatives).where(
            CryptoDerivatives.symbol.in_(["AVAX", "DOGE"])
        )
    )
    assert count == 2
