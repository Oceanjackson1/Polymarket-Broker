# data_pipeline/sports_collector.py
"""Sports market collector.

Fetches active sports markets from Polymarket Gamma.
When Dome API is available, also looks up matching Kalshi markets
and stores the Kalshi ticker alongside the Polymarket event.
"""
import logging
from datetime import datetime, date, UTC

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from data_pipeline.base import BaseCollector
from api.data.sports.models import SportsEvent
from core.polymarket.gamma_client import GammaClient
from core.dome.client import DomeClient, extract_list

logger = logging.getLogger(__name__)


def _parse_sport_slug(tags: list) -> str:
    """Extract sport slug from Polymarket market tags.
    Returns the first non-'sports' tag, or 'sports' as fallback.
    """
    for tag in tags:
        if tag and tag.lower() != "sports":
            return tag.lower()
    return "sports"


class SportsCollector(BaseCollector):
    name = "sports_collector"
    interval_seconds = 300

    def __init__(self, dome_client: DomeClient | None = None):
        self._dome = dome_client
        self._gamma = GammaClient()

    async def teardown(self) -> None:
        await self._gamma.close()

    async def _fetch_kalshi_matches(self, sport_slug: str) -> dict:
        """Build a lookup: polymarket_slug -> kalshi_ticker for today's matches."""
        if not self._dome:
            return {}
        try:
            resp = await self._dome.get_sport_matches(sport_slug, date.today().isoformat())
            matches = extract_list(resp)
            lookup = {}
            for m in matches:
                poly = m.get("polymarket", {})
                kalshi = m.get("kalshi", {})
                slug = poly.get("market_slug", "")
                ticker = kalshi.get("market_ticker", "") or kalshi.get("event_ticker", "")
                if slug and ticker:
                    lookup[slug] = ticker
            return lookup
        except Exception:
            logger.debug("kalshi matching failed for %s", sport_slug)
            return {}

    async def collect(self, db: AsyncSession) -> None:
        client = self._gamma
        offset = 0

        # Pre-fetch Kalshi match lookups for known sports.
        kalshi_lookups: dict[str, dict] = {}
        if self._dome:
            for sport in ("nba", "nfl", "mlb", "nhl"):
                kalshi_lookups[sport] = await self._fetch_kalshi_matches(sport)

        while True:
            markets = await client.get_markets(
                limit=100, offset=offset, tag="sports", active=True
            )
            if not markets:
                break
            for market in markets:
                sport_slug = _parse_sport_slug(market.get("tags") or [])
                market_id = market["id"]

                # Check for Kalshi match.
                kalshi_ticker = None
                slug = market.get("slug", "")
                sport_lookup = kalshi_lookups.get(sport_slug, {})
                if slug and sport_lookup:
                    kalshi_ticker = sport_lookup.get(slug)

                # Build resolution dict, optionally enriched with Kalshi info.
                resolution = market.get("resolution")
                if kalshi_ticker:
                    resolution = resolution or {}
                    if isinstance(resolution, dict):
                        resolution["kalshi_ticker"] = kalshi_ticker

                stmt = pg_insert(SportsEvent).values(
                    market_id=market_id,
                    sport_slug=sport_slug,
                    question=market.get("question", ""),
                    outcomes=market.get("outcomes") or [],
                    status="active" if market.get("active") else "closed",
                    resolution=resolution,
                    volume=market.get("volume"),
                    end_date=market.get("endDate"),
                    data_updated_at=datetime.now(UTC),
                ).on_conflict_do_update(
                    index_elements=["market_id"],
                    set_={
                        "sport_slug": sport_slug,
                        "question": market.get("question", ""),
                        "outcomes": market.get("outcomes") or [],
                        "status": "active" if market.get("active") else "closed",
                        "resolution": resolution,
                        "volume": market.get("volume"),
                        "end_date": market.get("endDate"),
                        "data_updated_at": datetime.now(UTC),
                    }
                )
                await db.execute(stmt)
            await db.commit()
            if len(markets) < 100:
                break
            offset += 100
