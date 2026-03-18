# data_pipeline/sports_collector.py
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from data_pipeline.base import BaseCollector
from api.data.sports.models import SportsEvent
from core.polymarket.gamma_client import GammaClient


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

    async def collect(self, db: AsyncSession) -> None:
        client = GammaClient()
        offset = 0
        while True:
            markets = await client.get_markets(
                limit=100, offset=offset, tag="sports", active=True
            )
            if not markets:
                break
            for market in markets:
                sport_slug = _parse_sport_slug(market.get("tags") or [])
                stmt = pg_insert(SportsEvent).values(
                    market_id=market["id"],
                    sport_slug=sport_slug,
                    question=market.get("question", ""),
                    outcomes=market.get("outcomes") or [],
                    status="active" if market.get("active") else "closed",
                    resolution=market.get("resolution"),
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
                        "resolution": market.get("resolution"),
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
