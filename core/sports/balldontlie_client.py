# core/sports/balldontlie_client.py
"""BallDontLie client — 20+ leagues, free tier."""
import logging
import httpx
from core.config import get_settings

logger = logging.getLogger(__name__)


class BallDontLieClient:
    """https://docs.balldontlie.io/"""

    def __init__(self):
        s = get_settings()
        self._key = s.balldontlie_api_key
        self._base = s.balldontlie_api_base
        self._headers = {"Authorization": self._key} if self._key else {}

    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=15.0, headers=self._headers) as c:
            r = await c.get(f"{self._base}/{endpoint}", params=params or {})
            r.raise_for_status()
            return r.json()

    async def get_games(self, dates: list[str] | None = None, seasons: list[int] | None = None,
                        team_ids: list[int] | None = None, cursor: int | None = None) -> dict:
        params = {}
        if dates:
            for d in dates:
                params.setdefault("dates[]", []).append(d)
        if seasons:
            for s in seasons:
                params.setdefault("seasons[]", []).append(s)
        if team_ids:
            for t in team_ids:
                params.setdefault("team_ids[]", []).append(t)
        if cursor:
            params["cursor"] = cursor
        return await self._get("games", params)

    async def get_teams(self, conference: str | None = None) -> dict:
        params = {}
        if conference:
            params["conference"] = conference
        return await self._get("teams", params)

    async def get_players(self, search: str | None = None, cursor: int | None = None) -> dict:
        params = {}
        if search:
            params["search"] = search
        if cursor:
            params["cursor"] = cursor
        return await self._get("players", params)

    async def get_stats(self, game_ids: list[int] | None = None) -> dict:
        params = {}
        if game_ids:
            for g in game_ids:
                params.setdefault("game_ids[]", []).append(g)
        return await self._get("stats", params)
