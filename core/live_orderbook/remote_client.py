"""HTTP client for the remote Binance Orderbook API on Tencent Cloud.

The server exposes a FastAPI at 127.0.0.1:18080 (inside the server).
We reach it via an SSH tunnel or direct URL configured in settings.

Also reads Polymarket BTC Up/Down orderbook CSVs via SSH/SCP.
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 15.0


class BinanceOrderbookClient:
    """Client for the remote Binance orderbook API (TimescaleDB-backed)."""

    def __init__(self, base_url: str, api_key: str = "", timeout: float = _DEFAULT_TIMEOUT):
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(
            base_url=base_url, timeout=timeout, headers=headers,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: dict | None = None) -> Any:
        resp = await self._client.get(path, params=_clean(params))
        resp.raise_for_status()
        return resp.json()

    # ── Health ───────────────────────────────────────────────────

    async def health(self) -> dict:
        return await self._get("/health")

    async def collector_health(self, market: str | None = None, symbol: str | None = None) -> dict:
        return await self._get("/v1/collector-health", {"market": market, "symbol": symbol})

    # ── Snapshots (aggregated) ───────────────────────────────────

    async def latest_summary(self, market: str, symbol: str) -> dict:
        return await self._get("/v1/orderbook/latest-summary", {"market": market, "symbol": symbol})

    async def latest_full_snapshot(
        self, market: str, symbol: str, snapshot_type: str | None = None,
    ) -> dict:
        return await self._get("/v1/orderbook/latest-full-snapshot", {
            "market": market, "symbol": symbol, "snapshot_type": snapshot_type,
        })

    async def snapshots(
        self,
        market: str,
        symbol: str,
        start_time: str | None = None,
        end_time: str | None = None,
        limit: int = 100,
    ) -> dict:
        return await self._get("/v1/orderbook/snapshots", {
            "market": market, "symbol": symbol,
            "start_time": start_time, "end_time": end_time, "limit": limit,
        })

    # ── Raw events ───────────────────────────────────────────────

    async def events(
        self,
        market: str,
        symbol: str,
        start_time: str | None = None,
        end_time: str | None = None,
        limit: int = 1000,
    ) -> dict:
        return await self._get("/v1/orderbook/events", {
            "market": market, "symbol": symbol,
            "start_time": start_time, "end_time": end_time, "limit": limit,
        })

    # ── Curated datasets ─────────────────────────────────────────

    async def curated(
        self,
        dataset: str,
        dt: str | None = None,
        timeframe: str | None = None,
        market_slug: str | None = None,
        limit: int = 500,
        offset: int = 0,
        columns: str | None = None,
    ) -> dict:
        return await self._get(f"/v1/curated/{dataset}", {
            "dt": dt, "timeframe": timeframe, "market_slug": market_slug,
            "limit": limit, "offset": offset, "columns": columns,
        })

    # ── Meta ─────────────────────────────────────────────────────

    async def meta_markets(self) -> dict:
        return await self._get("/v1/meta/markets")

    async def meta_files(self, **params) -> dict:
        return await self._get("/v1/meta/files", params)

    async def keysets_index(self) -> dict:
        return await self._get("/v1/keysets/index")


class PolymarketOrderbookClient:
    """Client for reading Polymarket BTC Up/Down orderbook data via SSH."""

    def __init__(self, ssh_host: str, ssh_key_path: str, data_dir: str):
        self._ssh_host = ssh_host
        self._ssh_key_path = ssh_key_path
        self._data_dir = data_dir

    async def list_windows(self, limit: int = 20) -> list[str]:
        """List recent orderbook time windows."""
        import asyncio
        cmd = (
            f'ssh -i "{self._ssh_key_path}" -o StrictHostKeyChecking=no '
            f'{self._ssh_host} '
            f'"ls -td {self._data_dir}/btc-updown-* | head -{limit}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        lines = stdout.decode().strip().split("\n")
        return [line.split("/")[-1] for line in lines if line]

    async def read_csv(self, window: str, file_prefix: str, max_lines: int = 500) -> str:
        """Read a CSV file from a specific time window via SSH."""
        import asyncio
        path = f"{self._data_dir}/{window}/{file_prefix}_{window}.csv"
        cmd = (
            f'ssh -i "{self._ssh_key_path}" -o StrictHostKeyChecking=no '
            f'{self._ssh_host} "head -{max_lines + 1} {path}"'
        )
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode()

    async def get_book_snapshots(self, window: str, max_lines: int = 500) -> list[dict]:
        raw = await self.read_csv(window, "book_snapshots", max_lines)
        return _csv_to_dicts(raw)

    async def get_price_changes(self, window: str, max_lines: int = 500) -> list[dict]:
        raw = await self.read_csv(window, "price_changes", max_lines)
        return _csv_to_dicts(raw)

    async def get_trades(self, window: str, max_lines: int = 500) -> list[dict]:
        raw = await self.read_csv(window, "trades", max_lines)
        return _csv_to_dicts(raw)


def _csv_to_dicts(csv_text: str) -> list[dict]:
    """Parse CSV text into list of dicts."""
    lines = csv_text.strip().split("\n")
    if len(lines) < 2:
        return []
    headers = lines[0].split(",")
    result = []
    for line in lines[1:]:
        vals = line.split(",")
        if len(vals) == len(headers):
            result.append(dict(zip(headers, vals)))
    return result


def _clean(params: dict | None) -> dict | None:
    if params is None:
        return None
    return {k: v for k, v in params.items() if v is not None}
