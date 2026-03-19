# core/sports/odds_api_client.py
"""The Odds API client — aggregated odds from 40+ bookmakers, 70+ sports."""
import logging
import httpx
from core.config import get_settings

logger = logging.getLogger(__name__)


class OddsApiClient:
    """https://the-odds-api.com/liveAPI/guides/v4/"""

    def __init__(self):
        s = get_settings()
        self._key = s.odds_api_key
        self._base = s.odds_api_base

    async def get_sports(self) -> list[dict]:
        """List all available sports."""
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.get(f"{self._base}/sports", params={"apiKey": self._key})
            r.raise_for_status()
            return r.json()

    async def get_odds(self, sport: str, regions: str = "us,eu,uk",
                       markets: str = "h2h,spreads,totals", odds_format: str = "decimal") -> list[dict]:
        """Get odds for a sport. sport = sport_key from get_sports()."""
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.get(f"{self._base}/sports/{sport}/odds", params={
                "apiKey": self._key, "regions": regions,
                "markets": markets, "oddsFormat": odds_format,
            })
            r.raise_for_status()
            return r.json()

    async def get_scores(self, sport: str, days_from: int = 1) -> list[dict]:
        """Get live & recent scores."""
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.get(f"{self._base}/sports/{sport}/scores", params={
                "apiKey": self._key, "daysFrom": days_from,
            })
            r.raise_for_status()
            return r.json()

    async def get_event_odds(self, sport: str, event_id: str,
                             regions: str = "us,eu", markets: str = "h2h") -> dict:
        """Get odds for a specific event."""
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.get(f"{self._base}/sports/{sport}/events/{event_id}/odds", params={
                "apiKey": self._key, "regions": regions, "markets": markets,
            })
            r.raise_for_status()
            return r.json()
