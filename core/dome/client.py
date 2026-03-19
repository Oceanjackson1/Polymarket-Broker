"""Unified async REST client for the Dome API (https://api.domeapi.io/v1)."""

import logging
from typing import Any

import httpx

from core.dome.key_pool import DomeKeyPool

logger = logging.getLogger(__name__)

_DEFAULT_BASE = "https://api.domeapi.io/v1"
_DEFAULT_TIMEOUT = 30.0


class DomeClient:
    """High-level, async wrapper around the Dome API.

    Every request automatically picks a key from the pool and attaches
    a Bearer token. On HTTP 429 the offending key enters cooldown and
    the request is retried once with the next key.
    """

    def __init__(
        self,
        key_pool: DomeKeyPool,
        base_url: str = _DEFAULT_BASE,
        timeout: float = _DEFAULT_TIMEOUT,
    ):
        self._pool = key_pool
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    # ── low-level request helpers ────────────────────────────────

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
    ) -> Any:
        """Execute *method* on *path* with automatic key rotation + 429 retry."""
        key = self._pool.next_key()
        resp = await self._client.request(
            method,
            path,
            params=_clean_params(params),
            json=json,
            headers={"Authorization": f"Bearer {key}"},
        )
        if resp.status_code == 429:
            self._pool.report_rate_limit(key)
            key = self._pool.next_key()
            resp = await self._client.request(
                method,
                path,
                params=_clean_params(params),
                json=json,
                headers={"Authorization": f"Bearer {key}"},
            )
        resp.raise_for_status()
        return resp.json()

    async def _get(self, path: str, params: dict | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def _post(self, path: str, json: dict | None = None) -> Any:
        return await self._request("POST", path, json=json)

    # ══════════════════════════════════════════════════════════════
    #  Polymarket — Markets & Events
    # ══════════════════════════════════════════════════════════════

    async def get_markets(
        self,
        *,
        market_slugs: list[str] | None = None,
        event_slugs: list[str] | None = None,
        condition_ids: list[str] | None = None,
        token_ids: list[str] | None = None,
        tags: list[str] | None = None,
        search: str | None = None,
        status: str | None = None,
        min_volume: int | None = None,
        limit: int = 100,
        pagination_key: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict:
        params: dict[str, Any] = {"limit": limit}
        _add_list(params, "market_slug[]", market_slugs)
        _add_list(params, "event_slug[]", event_slugs)
        _add_list(params, "condition_id[]", condition_ids)
        _add_list(params, "token_id[]", token_ids)
        _add_list(params, "tags[]", tags)
        _add_opt(params, "search", search)
        _add_opt(params, "status", status)
        _add_opt(params, "min_volume", min_volume)
        _add_opt(params, "pagination_key", pagination_key)
        _add_opt(params, "start_time", start_time)
        _add_opt(params, "end_time", end_time)
        return await self._get("/polymarket/markets", params)

    async def get_events(
        self,
        *,
        event_slug: str | None = None,
        tags: list[str] | None = None,
        status: str | None = None,
        include_markets: bool | None = None,
        limit: int = 100,
        pagination_key: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict:
        params: dict[str, Any] = {"limit": limit}
        _add_opt(params, "event_slug", event_slug)
        _add_list(params, "tags[]", tags)
        _add_opt(params, "status", status)
        _add_opt(params, "include_markets", include_markets)
        _add_opt(params, "pagination_key", pagination_key)
        _add_opt(params, "start_time", start_time)
        _add_opt(params, "end_time", end_time)
        return await self._get("/polymarket/events", params)

    async def get_market_price(
        self, token_id: str, *, at_time: int | None = None
    ) -> dict:
        params: dict[str, Any] = {}
        _add_opt(params, "at_time", at_time)
        return await self._get(f"/polymarket/market-price/{token_id}", params)

    async def get_candlesticks(
        self,
        condition_id: str,
        *,
        start_time: int,
        end_time: int,
        interval: int = 60,
    ) -> dict:
        return await self._get(
            f"/polymarket/candlesticks/{condition_id}",
            {"start_time": start_time, "end_time": end_time, "interval": interval},
        )

    async def get_orders(
        self,
        *,
        market_slug: str | None = None,
        condition_id: str | None = None,
        token_id: str | None = None,
        user: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
        pagination_key: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"limit": limit}
        _add_opt(params, "market_slug", market_slug)
        _add_opt(params, "condition_id", condition_id)
        _add_opt(params, "token_id", token_id)
        _add_opt(params, "user", user)
        _add_opt(params, "start_time", start_time)
        _add_opt(params, "end_time", end_time)
        _add_opt(params, "pagination_key", pagination_key)
        return await self._get("/polymarket/orders", params)

    async def get_orderbook_snapshots(
        self,
        token_id: str,
        *,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
        pagination_key: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"token_id": token_id, "limit": limit}
        _add_opt(params, "start_time", start_time)
        _add_opt(params, "end_time", end_time)
        _add_opt(params, "pagination_key", pagination_key)
        return await self._get("/polymarket/orderbooks", params)

    async def get_activity(
        self,
        *,
        user: str | None = None,
        market_slug: str | None = None,
        condition_id: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
        pagination_key: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"limit": limit}
        _add_opt(params, "user", user)
        _add_opt(params, "market_slug", market_slug)
        _add_opt(params, "condition_id", condition_id)
        _add_opt(params, "start_time", start_time)
        _add_opt(params, "end_time", end_time)
        _add_opt(params, "pagination_key", pagination_key)
        return await self._get("/polymarket/activity", params)

    # ══════════════════════════════════════════════════════════════
    #  Polymarket — Wallet & Positions
    # ══════════════════════════════════════════════════════════════

    async def get_wallet(
        self,
        *,
        eoa: str | None = None,
        proxy: str | None = None,
        handle: str | None = None,
        with_metrics: bool | None = None,
    ) -> dict:
        params: dict[str, Any] = {}
        _add_opt(params, "eoa", eoa)
        _add_opt(params, "proxy", proxy)
        _add_opt(params, "handle", handle)
        _add_opt(params, "with_metrics", with_metrics)
        return await self._get("/polymarket/wallet", params)

    async def get_wallet_pnl(
        self,
        wallet_address: str,
        *,
        granularity: str = "day",
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict:
        params: dict[str, Any] = {"granularity": granularity}
        _add_opt(params, "start_time", start_time)
        _add_opt(params, "end_time", end_time)
        return await self._get(
            f"/polymarket/wallet/pnl/{wallet_address}", params
        )

    async def get_positions(
        self,
        wallet_address: str,
        *,
        limit: int = 100,
        pagination_key: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"limit": limit}
        _add_opt(params, "pagination_key", pagination_key)
        return await self._get(
            f"/polymarket/positions/wallet/{wallet_address}", params
        )

    # ══════════════════════════════════════════════════════════════
    #  Kalshi
    # ══════════════════════════════════════════════════════════════

    async def get_kalshi_markets(
        self,
        *,
        market_tickers: list[str] | None = None,
        event_tickers: list[str] | None = None,
        search: str | None = None,
        status: str | None = None,
        min_volume: int | None = None,
        limit: int = 100,
        pagination_key: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"limit": limit}
        _add_list(params, "market_ticker[]", market_tickers)
        _add_list(params, "event_ticker[]", event_tickers)
        _add_opt(params, "search", search)
        _add_opt(params, "status", status)
        _add_opt(params, "min_volume", min_volume)
        _add_opt(params, "pagination_key", pagination_key)
        return await self._get("/kalshi/markets", params)

    async def get_kalshi_price(
        self, market_ticker: str, *, at_time: int | None = None
    ) -> dict:
        params: dict[str, Any] = {}
        _add_opt(params, "at_time", at_time)
        return await self._get(f"/kalshi/market-price/{market_ticker}", params)

    async def get_kalshi_trades(
        self,
        *,
        ticker: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
        pagination_key: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"limit": limit}
        _add_opt(params, "ticker", ticker)
        _add_opt(params, "start_time", start_time)
        _add_opt(params, "end_time", end_time)
        _add_opt(params, "pagination_key", pagination_key)
        return await self._get("/kalshi/trades", params)

    async def get_kalshi_orderbook_snapshots(
        self,
        ticker: str,
        *,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
        pagination_key: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"ticker": ticker, "limit": limit}
        _add_opt(params, "start_time", start_time)
        _add_opt(params, "end_time", end_time)
        _add_opt(params, "pagination_key", pagination_key)
        return await self._get("/kalshi/orderbooks", params)

    # ══════════════════════════════════════════════════════════════
    #  Cross-Platform Matching
    # ══════════════════════════════════════════════════════════════

    async def get_matching_markets(
        self,
        *,
        polymarket_slugs: list[str] | None = None,
        kalshi_tickers: list[str] | None = None,
    ) -> dict:
        params: dict[str, Any] = {}
        _add_list(params, "polymarket_market_slug[]", polymarket_slugs)
        _add_list(params, "kalshi_event_ticker[]", kalshi_tickers)
        return await self._get("/matching-markets/sports", params)

    async def get_sport_matches(self, sport: str, date: str) -> dict:
        """Get cross-platform markets for a sport on a date (YYYY-MM-DD)."""
        return await self._get(
            f"/matching-markets/sports/{sport}", {"date": date}
        )

    # ══════════════════════════════════════════════════════════════
    #  Crypto Prices
    # ══════════════════════════════════════════════════════════════

    async def get_binance_price(
        self,
        currency: str,
        *,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
        pagination_key: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"currency": currency, "limit": limit}
        _add_opt(params, "start_time", start_time)
        _add_opt(params, "end_time", end_time)
        _add_opt(params, "pagination_key", pagination_key)
        return await self._get("/crypto-prices/binance", params)

    async def get_chainlink_price(
        self,
        currency: str,
        *,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 100,
        pagination_key: str | None = None,
    ) -> dict:
        params: dict[str, Any] = {"currency": currency, "limit": limit}
        _add_opt(params, "start_time", start_time)
        _add_opt(params, "end_time", end_time)
        _add_opt(params, "pagination_key", pagination_key)
        return await self._get("/crypto-prices/chainlink", params)

    # ══════════════════════════════════════════════════════════════
    #  Order Router
    # ══════════════════════════════════════════════════════════════

    async def place_order(
        self,
        *,
        user_id: str,
        market_id: str,
        side: str,
        size: float,
        price: float,
        signer: str,
        order_type: str = "GTC",
        neg_risk: bool = False,
        wallet_type: str | None = None,
        funder_address: str | None = None,
    ) -> dict:
        body: dict[str, Any] = {
            "userId": user_id,
            "marketId": market_id,
            "side": side,
            "size": size,
            "price": price,
            "signer": signer,
            "orderType": order_type,
            "negRisk": neg_risk,
        }
        _add_opt(body, "walletType", wallet_type)
        _add_opt(body, "funderAddress", funder_address)
        return await self._post("/polymarket/placeOrder", body)


# ── parameter helpers ────────────────────────────────────────────


def _add_opt(d: dict, key: str, val: Any) -> None:
    if val is not None:
        d[key] = val


def _add_list(d: dict, key: str, vals: list | None) -> None:
    if vals:
        d[key] = vals


def _clean_params(params: dict | None) -> dict | None:
    """Remove None values so httpx doesn't send ?key=None."""
    if params is None:
        return None
    return {k: v for k, v in params.items() if v is not None}


def extract_list(resp: Any) -> list:
    """Extract the data list from a Dome API response.

    Dome endpoints use different wrapper keys:
      - /polymarket/markets   → {"markets": [...]}
      - /polymarket/events    → {"events": [...]}
      - /kalshi/markets       → {"markets": [...]}
      - /crypto-prices/*      → {"prices": [...]}
      - others                → {"data": [...]}
    This helper tries common keys and falls back gracefully.
    """
    if isinstance(resp, list):
        return resp
    if not isinstance(resp, dict):
        return []
    for key in ("markets", "events", "data", "prices", "orders", "trades", "positions", "orderbooks"):
        if key in resp and isinstance(resp[key], list):
            return resp[key]
    return []
