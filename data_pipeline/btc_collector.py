# data_pipeline/btc_collector.py
"""BTC price + prediction collector.

Primary data source: Dome API (Binance price feed).
Fallback: CoinGecko (if Dome is unavailable or not configured).
Market data: Dome markets API (replaces Gamma for BTC prediction markets).
"""
import logging
from datetime import datetime, UTC
from decimal import Decimal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from data_pipeline.base import BaseCollector
from api.data.btc.models import BtcSnapshot
from core.polymarket.gamma_client import GammaClient
from core.dome.client import DomeClient
from core.config import get_settings as _get_settings

logger = logging.getLogger(__name__)

COINGECKO_URL = (
    f"{_get_settings().coingecko_api_base}/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
)
TIMEFRAMES = ["5m", "15m", "1h", "4h"]


def _find_market_for_timeframe(timeframe: str, markets: list) -> dict | None:
    """Find the Polymarket BTC prediction market for the given timeframe."""
    for m in markets:
        q = (m.get("question", "") or m.get("title", "")).lower()
        if timeframe in q:
            return m
    return None


def _parse_prob(market: dict) -> Decimal | None:
    # Gamma format
    prices = market.get("outcomePrices", [])
    if prices:
        try:
            return Decimal(str(prices[0]))
        except Exception:
            pass
    # Dome format: side_a.price or direct price field
    side_a = market.get("side_a", {})
    if side_a and side_a.get("id"):
        return None  # price needs separate fetch
    return None


class BtcCollector(BaseCollector):
    name = "btc_collector"
    interval_seconds = 30

    def __init__(self, dome_client: DomeClient | None = None):
        self._dome = dome_client
        self._gamma = GammaClient()

    async def teardown(self) -> None:
        await self._gamma.close()

    async def _fetch_btc_price(self) -> Decimal:
        """Fetch BTC/USD price. Primary: Dome/Binance, fallback: CoinGecko."""
        if self._dome:
            try:
                resp = await self._dome.get_binance_price("btcusdt", limit=1)
                data = resp.get("data", []) if isinstance(resp, dict) else resp
                if data:
                    return Decimal(str(data[0].get("value", data[0].get("price", 0))))
            except Exception:
                logger.debug("dome binance price failed, falling back to coingecko")

        # Fallback: CoinGecko
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(COINGECKO_URL)
            resp.raise_for_status()
            data = resp.json()
        return Decimal(str(data["bitcoin"]["usd"]))

    async def _fetch_btc_markets(self) -> list:
        """Fetch BTC prediction markets. Primary: Dome, fallback: Gamma."""
        if self._dome:
            try:
                resp = await self._dome.get_markets(tags=["crypto"], status="open", limit=20)
                markets = resp.get("data", []) if isinstance(resp, dict) else resp
                if markets:
                    return markets
            except Exception:
                logger.debug("dome markets failed, falling back to gamma")

        return await self._gamma.get_markets(limit=20, tag="crypto", active=True)

    async def collect(self, db: AsyncSession) -> None:
        price_usd = await self._fetch_btc_price()
        btc_markets = await self._fetch_btc_markets()

        for timeframe in TIMEFRAMES:
            matched = _find_market_for_timeframe(timeframe, btc_markets)
            market_id = (matched.get("id") or matched.get("condition_id")) if matched else None
            prediction_prob = _parse_prob(matched) if matched else None
            volume = Decimal(str(matched.get("volume", 0) or matched.get("volume_24h", 0) or 0)) if matched else None

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
