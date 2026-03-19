# data_pipeline/dome_market_collector.py
"""Collects enriched market snapshots (price + candlestick + depth) via Dome API."""

import logging
import time
from datetime import datetime, UTC
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from core.dome.client import DomeClient, extract_list
from data_pipeline.base import BaseCollector
from api.data.dome.models import MarketSnapshot

logger = logging.getLogger(__name__)


class DomeMarketCollector(BaseCollector):
    name = "dome_market_collector"
    interval_seconds = 60

    def __init__(self, dome_client: DomeClient):
        self._dome = dome_client

    async def collect(self, db: AsyncSession) -> None:
        now = int(time.time())
        one_hour_ago = now - 3600

        # 1. Fetch high-volume open markets.
        resp = await self._dome.get_markets(status="open", min_volume=10000, limit=50)
        markets = extract_list(resp)

        for m in markets:
            slug = m.get("market_slug", "")
            condition_id = m.get("condition_id", "")
            side_a = m.get("side_a", {})
            token_id = side_a.get("id", "")
            if not (slug and condition_id and token_id):
                continue

            # 2. Fetch current price.
            try:
                price_resp = await self._dome.get_market_price(token_id)
                price = Decimal(str(price_resp.get("price", 0)))
            except Exception:
                logger.debug("skipping price for %s", slug)
                continue

            # 3. Fetch 1-hour candlestick (single bar → OHLC).
            ohlc: dict = {}
            try:
                candle_resp = await self._dome.get_candlesticks(
                    condition_id, start_time=one_hour_ago, end_time=now, interval=60,
                )
                candles = extract_list(candle_resp)
                if candles:
                    last = candles[-1]
                    ohlc = {
                        "open": Decimal(str(last.get("open", 0))),
                        "high": Decimal(str(last.get("high", 0))),
                        "low": Decimal(str(last.get("low", 0))),
                        "close": Decimal(str(last.get("close", 0))),
                    }
            except Exception:
                logger.debug("no candlestick for %s", slug)

            # 4. Fetch latest orderbook snapshot for depth.
            bid_depth = ask_depth = None
            try:
                ob_resp = await self._dome.get_orderbook_snapshots(token_id, limit=1)
                obs = extract_list(ob_resp)
                if obs:
                    latest = obs[0]
                    bids = latest.get("bids", [])
                    asks = latest.get("asks", [])
                    bid_depth = Decimal(str(sum(float(b[1]) for b in bids))) if bids else None
                    ask_depth = Decimal(str(sum(float(a[1]) for a in asks))) if asks else None
            except Exception:
                logger.debug("no orderbook for %s", slug)

            snapshot = MarketSnapshot(
                market_slug=slug,
                condition_id=condition_id,
                token_id=token_id,
                price=price,
                volume_24h=Decimal(str(m.get("volume_24h", 0) or 0)),
                open=ohlc.get("open"),
                high=ohlc.get("high"),
                low=ohlc.get("low"),
                close=ohlc.get("close"),
                bid_depth=bid_depth,
                ask_depth=ask_depth,
                recorded_at=datetime.now(UTC),
            )
            db.add(snapshot)

        await db.commit()
        logger.debug("dome_market_collector: stored %d snapshots", len(markets))
