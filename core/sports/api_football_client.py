# core/sports/api_football_client.py
"""API-Football client — 2000+ leagues, 12 sports via api-sports.io."""
import logging
import httpx
from core.config import get_settings

logger = logging.getLogger(__name__)


class ApiFootballClient:
    """https://www.api-football.com/documentation-v3"""

    def __init__(self):
        s = get_settings()
        self._key = s.api_football_key
        self._base = s.api_football_base
        self._headers = {"x-apisports-key": self._key}

    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=15.0, headers=self._headers) as c:
            r = await c.get(f"{self._base}/{endpoint}", params=params or {})
            r.raise_for_status()
            return r.json()

    async def get_fixtures(self, league: int | None = None, date: str | None = None,
                           live: str | None = None, season: int | None = None) -> list[dict]:
        """Get fixtures/matches. live='all' for live games."""
        params = {}
        if league:
            params["league"] = league
        if date:
            params["date"] = date
        if live:
            params["live"] = live
        if season:
            params["season"] = season
        data = await self._get("fixtures", params)
        return data.get("response", [])

    async def get_leagues(self, country: str | None = None, type_: str | None = None) -> list[dict]:
        params = {}
        if country:
            params["country"] = country
        if type_:
            params["type"] = type_
        data = await self._get("leagues", params)
        return data.get("response", [])

    async def get_odds(self, fixture: int | None = None, league: int | None = None,
                       date: str | None = None) -> list[dict]:
        params = {}
        if fixture:
            params["fixture"] = fixture
        if league:
            params["league"] = league
        if date:
            params["date"] = date
        data = await self._get("odds", params)
        return data.get("response", [])

    async def get_predictions(self, fixture: int) -> list[dict]:
        data = await self._get("predictions", {"fixture": fixture})
        return data.get("response", [])

    async def get_standings(self, league: int, season: int) -> list[dict]:
        data = await self._get("standings", {"league": league, "season": season})
        return data.get("response", [])

    async def get_live_scores(self) -> list[dict]:
        return await self.get_fixtures(live="all")
