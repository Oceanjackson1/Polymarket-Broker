# core/sports/football_data_client.py
"""football-data.org client — 12 competitions free forever."""
import logging
import httpx
from core.config import get_settings

logger = logging.getLogger(__name__)

# Free tier: 12 competitions
FREE_COMPETITIONS = [
    "PL",   # Premier League
    "BL1",  # Bundesliga
    "SA",   # Serie A
    "PD",   # La Liga
    "FL1",  # Ligue 1
    "DED",  # Eredivisie
    "PPL",  # Primeira Liga
    "ELC",  # Championship
    "BSA",  # Brazilian Serie A
    "CL",   # Champions League
    "WC",   # World Cup
    "EC",   # European Championship
]


class FootballDataClient:
    """https://www.football-data.org/documentation/api"""

    def __init__(self):
        s = get_settings()
        self._key = s.football_data_key
        self._base = s.football_data_base
        self._headers = {"X-Auth-Token": self._key} if self._key else {}

    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=15.0, headers=self._headers) as c:
            r = await c.get(f"{self._base}/{endpoint}", params=params or {})
            r.raise_for_status()
            return r.json()

    async def get_competitions(self) -> list[dict]:
        data = await self._get("competitions")
        return data.get("competitions", [])

    async def get_matches(self, competition: str, matchday: int | None = None,
                          date_from: str | None = None, date_to: str | None = None) -> list[dict]:
        params = {}
        if matchday:
            params["matchday"] = matchday
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        data = await self._get(f"competitions/{competition}/matches", params)
        return data.get("matches", [])

    async def get_standings(self, competition: str) -> list[dict]:
        data = await self._get(f"competitions/{competition}/standings")
        return data.get("standings", [])

    async def get_scorers(self, competition: str) -> list[dict]:
        data = await self._get(f"competitions/{competition}/scorers")
        return data.get("scorers", [])

    async def get_today_matches(self) -> list[dict]:
        """All matches today across all free competitions."""
        data = await self._get("matches", {"status": "SCHEDULED,IN_PLAY,PAUSED,FINISHED"})
        return data.get("matches", [])
