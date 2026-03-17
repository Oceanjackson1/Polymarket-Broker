import httpx
from typing import Any
from core.config import get_settings

settings = get_settings()


class GammaClient:
    def __init__(self, base_url: str | None = None):
        self._base_url = base_url or settings.polymarket_gamma_host
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=30.0)

    async def _get(self, path: str, params: dict = None) -> Any:
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_markets(self, limit: int = 100, offset: int = 0, **filters) -> list:
        return await self._get("/markets", params={"limit": limit, "offset": offset, **filters})

    async def get_market(self, market_id: str) -> dict:
        return await self._get(f"/markets/{market_id}")

    async def get_events(self, **filters) -> list:
        return await self._get("/events", params=filters)

    async def close(self):
        await self._client.aclose()
