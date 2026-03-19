# data_pipeline/btc_collector.py
from datetime import datetime, UTC
from decimal import Decimal
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from data_pipeline.base import BaseCollector
from api.data.btc.models import BtcSnapshot
from core.polymarket.gamma_client import GammaClient

from core.config import get_settings as _get_settings

COINGECKO_URL = (
    f"{_get_settings().coingecko_api_base}/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
)
TIMEFRAMES = ["5m", "15m", "1h", "4h"]


def _find_market_for_timeframe(timeframe: str, markets: list) -> dict | None:
    """Find the Polymarket BTC prediction market for the given timeframe."""
    for m in markets:
        q = m.get("question", "").lower()
        if timeframe in q:
            return m
    return None


def _parse_prob(market: dict) -> Decimal | None:
    prices = market.get("outcomePrices", [])
    try:
        return Decimal(str(prices[0]))
    except Exception:
        return None


class BtcCollector(BaseCollector):
    name = "btc_collector"
    interval_seconds = 30

    def __init__(self):
        self._gamma = GammaClient()

    async def teardown(self) -> None:
        await self._gamma.close()

    async def collect(self, db: AsyncSession) -> None:
        # 1. Fetch BTC price from CoinGecko
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(COINGECKO_URL)
            resp.raise_for_status()
            data = resp.json()

        price_usd = Decimal(str(data["bitcoin"]["usd"]))

        # 2. Fetch BTC prediction markets from Polymarket Gamma
        btc_markets = await self._gamma.get_markets(limit=20, tag="crypto", active=True)

        # 3. Append one row per timeframe
        for timeframe in TIMEFRAMES:
            matched = _find_market_for_timeframe(timeframe, btc_markets)
            market_id = matched["id"] if matched else None
            prediction_prob = _parse_prob(matched) if matched else None
            volume = Decimal(str(matched.get("volume", 0) or 0)) if matched else None

            snapshot = BtcSnapshot(
                timeframe=timeframe,
                price_usd=price_usd,
                market_id=market_id,
                prediction_prob=prediction_prob,
                volume=volume,
                recorded_at=datetime.now(UTC),
            )
            db.add(snapshot)

        await db.commit()
