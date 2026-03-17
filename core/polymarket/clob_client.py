import httpx
from typing import Any
from core.config import get_settings

settings = get_settings()


class ClobClient:
    def __init__(self, base_url: str | None = None):
        self._base_url = base_url or settings.polymarket_clob_host
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=30.0)

    async def _get(self, path: str, params: dict = None) -> Any:
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, json: dict, headers: dict = None) -> Any:
        resp = await self._client.post(path, json=json, headers=headers or {})
        resp.raise_for_status()
        return resp.json()

    async def get_orderbook(self, token_id: str) -> dict:
        return await self._get("/book", params={"token_id": token_id})

    async def get_midpoint(self, token_id: str) -> dict:
        return await self._get("/midpoint", params={"token_id": token_id})

    async def get_trades(self, market_id: str, **params) -> list:
        return await self._get("/trades", params={"market": market_id, **params})

    async def post_order(self, signed_order: dict, api_key: str) -> dict:
        import time
        headers = {
            "POLY_API_KEY": api_key,
            "POLY_TIMESTAMP": str(int(time.time())),
        }
        return await self._post("/order", json=signed_order, headers=headers)

    async def cancel_order(self, order_id: str, api_key: str) -> dict:
        import time
        headers = {"POLY_API_KEY": api_key, "POLY_TIMESTAMP": str(int(time.time()))}
        return await self._post("/cancel", json={"orderID": order_id}, headers=headers)

    async def close(self):
        await self._client.aclose()
