# data_pipeline/kalshi_collector.py
"""Collects Kalshi markets and computes cross-platform spreads vs Polymarket."""

import logging
from datetime import datetime, date, UTC
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from core.dome.client import DomeClient
from data_pipeline.base import BaseCollector
from api.data.dome.models import CrossPlatformSpread

logger = logging.getLogger(__name__)

SPORTS = ["nfl", "nba", "mlb", "nhl", "cfb", "cbb", "pga", "tennis"]


class KalshiCollector(BaseCollector):
    name = "kalshi_collector"
    interval_seconds = 120

    def __init__(self, dome_client: DomeClient):
        self._dome = dome_client

    async def collect(self, db: AsyncSession) -> None:
        today = date.today().isoformat()
        count = 0

        for sport in SPORTS:
            try:
                resp = await self._dome.get_sport_matches(sport, today)
            except Exception:
                logger.debug("no matches for %s on %s", sport, today)
                continue

            matches = resp.get("data", []) if isinstance(resp, dict) else resp
            if not matches:
                continue

            for match in matches:
                poly = match.get("polymarket", {})
                kalshi = match.get("kalshi", {})
                poly_slug = poly.get("market_slug", "")
                kalshi_ticker = kalshi.get("market_ticker", "") or kalshi.get("event_ticker", "")
                if not (poly_slug and kalshi_ticker):
                    continue

                # Fetch prices for both sides.
                try:
                    poly_token = poly.get("token_id") or poly.get("side_a", {}).get("id", "")
                    if not poly_token:
                        continue
                    poly_price_resp = await self._dome.get_market_price(poly_token)
                    poly_price = Decimal(str(poly_price_resp.get("price", 0)))

                    kalshi_price_resp = await self._dome.get_kalshi_price(kalshi_ticker)
                    # Kalshi returns yes/no; use yes side.
                    kalshi_yes = kalshi_price_resp.get("yes", kalshi_price_resp)
                    kalshi_price = Decimal(str(kalshi_yes.get("price", 0)))
                except Exception:
                    logger.debug("price fetch failed for %s / %s", poly_slug, kalshi_ticker)
                    continue

                if poly_price == 0 or kalshi_price == 0:
                    continue

                spread = abs(poly_price - kalshi_price)
                spread_bps = int(spread * 10000)
                direction = "POLY_CHEAP" if poly_price < kalshi_price else "KALSHI_CHEAP"
                if spread_bps == 0:
                    direction = "EQUAL"

                row = CrossPlatformSpread(
                    polymarket_slug=poly_slug,
                    kalshi_ticker=kalshi_ticker,
                    sport=sport,
                    poly_price=poly_price,
                    kalshi_price=kalshi_price,
                    spread_bps=spread_bps,
                    direction=direction,
                    recorded_at=datetime.now(UTC),
                )
                db.add(row)
                count += 1

        await db.commit()
        logger.debug("kalshi_collector: stored %d spreads", count)
