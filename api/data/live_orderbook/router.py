# api/data/live_orderbook/router.py
"""API routes for live BTC orderbook data from Tencent Cloud server.

Two data sources:
1. Binance BTCUSDT orderbook (spot + futures) — TimescaleDB via HTTP API
2. Polymarket BTC Up/Down 5-min markets — CSV files via SSH
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from api.deps import get_current_user_from_api_key, require_scope

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data/live-orderbook", tags=["data-live-orderbook"])


def _get_binance_client(request: Request):
    client = getattr(request.app.state, "binance_ob_client", None)
    if not client:
        raise HTTPException(503, detail="BINANCE_ORDERBOOK_NOT_CONFIGURED")
    return client


def _get_polymarket_ob_client(request: Request):
    client = getattr(request.app.state, "polymarket_ob_client", None)
    if not client:
        raise HTTPException(503, detail="POLYMARKET_ORDERBOOK_NOT_CONFIGURED")
    return client


# ══════════════════════════════════════════════════════════════════
#  Binance BTC Orderbook (Spot + Futures)
# ══════════════════════════════════════════════════════════════════

@router.get("/binance/health")
async def binance_health(request: Request, auth: dict = Depends(get_current_user_from_api_key)):
    """Health check for the remote Binance orderbook collector."""
    require_scope(auth, "data:read")
    client = _get_binance_client(request)
    return await client.health()


@router.get("/binance/collector-health")
async def binance_collector_health(
    request: Request,
    market: str | None = Query(default=None, regex="^(spot|futures)$"),
    auth: dict = Depends(get_current_user_from_api_key),
):
    """Collector status per market/symbol."""
    require_scope(auth, "data:read")
    client = _get_binance_client(request)
    return await client.collector_health(market=market, symbol="BTCUSDT")


@router.get("/binance/latest")
async def binance_latest(
    request: Request,
    market: str = Query(default="spot", regex="^(spot|futures)$"),
    auth: dict = Depends(get_current_user_from_api_key),
):
    """Latest aggregated orderbook summary (best bid/ask, spread, depth)."""
    require_scope(auth, "data:read")
    client = _get_binance_client(request)
    return await client.latest_summary(market=market, symbol="BTCUSDT")


@router.get("/binance/full-snapshot")
async def binance_full_snapshot(
    request: Request,
    market: str = Query(default="spot", regex="^(spot|futures)$"),
    auth: dict = Depends(get_current_user_from_api_key),
):
    """Latest full orderbook snapshot with all bid/ask levels (raw depth data)."""
    require_scope(auth, "data:read")
    client = _get_binance_client(request)
    return await client.latest_full_snapshot(market=market, symbol="BTCUSDT")


@router.get("/binance/snapshots")
async def binance_snapshots(
    request: Request,
    market: str = Query(default="spot", regex="^(spot|futures)$"),
    start_time: str | None = Query(default=None, description="ISO 8601 datetime"),
    end_time: str | None = Query(default=None, description="ISO 8601 datetime"),
    limit: int = Query(default=100, ge=1, le=1000),
    auth: dict = Depends(get_current_user_from_api_key),
):
    """Historical full orderbook snapshots with time range filter."""
    require_scope(auth, "data:read")
    client = _get_binance_client(request)
    return await client.snapshots(
        market=market, symbol="BTCUSDT",
        start_time=start_time, end_time=end_time, limit=limit,
    )


@router.get("/binance/events")
async def binance_events(
    request: Request,
    market: str = Query(default="spot", regex="^(spot|futures)$"),
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    limit: int = Query(default=1000, ge=1, le=10000),
    auth: dict = Depends(get_current_user_from_api_key),
):
    """Raw orderbook diff events (L2 updates)."""
    require_scope(auth, "data:read")
    client = _get_binance_client(request)
    return await client.events(
        market=market, symbol="BTCUSDT",
        start_time=start_time, end_time=end_time, limit=limit,
    )


@router.get("/binance/curated/{dataset}")
async def binance_curated(
    request: Request,
    dataset: str,
    dt: str | None = Query(default=None),
    timeframe: str | None = Query(default=None),
    market_slug: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
    columns: str | None = Query(default=None, description="Comma-separated column names"),
    auth: dict = Depends(get_current_user_from_api_key),
):
    """Curated datasets (book_snapshots, price_changes, etc.)."""
    require_scope(auth, "data:read")
    client = _get_binance_client(request)
    return await client.curated(
        dataset, dt=dt, timeframe=timeframe, market_slug=market_slug,
        limit=limit, offset=offset, columns=columns,
    )


@router.get("/binance/meta/markets")
async def binance_meta_markets(
    request: Request,
    auth: dict = Depends(get_current_user_from_api_key),
):
    """Available markets and metadata."""
    require_scope(auth, "data:read")
    client = _get_binance_client(request)
    return await client.meta_markets()


# ══════════════════════════════════════════════════════════════════
#  Polymarket BTC Up/Down Orderbook
# ══════════════════════════════════════════════════════════════════

@router.get("/polymarket/windows")
async def polymarket_windows(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    auth: dict = Depends(get_current_user_from_api_key),
):
    """List recent BTC Up/Down orderbook recording time windows."""
    require_scope(auth, "data:read")
    client = _get_polymarket_ob_client(request)
    windows = await client.list_windows(limit=limit)
    return {"count": len(windows), "windows": windows}


@router.get("/polymarket/{window}/book-snapshots")
async def polymarket_book_snapshots(
    request: Request,
    window: str,
    max_lines: int = Query(default=500, ge=1, le=5000),
    auth: dict = Depends(get_current_user_from_api_key),
):
    """Orderbook depth snapshots for a specific time window.

    Each row: snapshot_seq, server_ts_ms, asset_id, outcome (Up/Down), side (bid/ask), price, size, level_index.
    """
    require_scope(auth, "data:read")
    client = _get_polymarket_ob_client(request)
    data = await client.get_book_snapshots(window, max_lines)
    return {"window": window, "count": len(data), "data": data}


@router.get("/polymarket/{window}/price-changes")
async def polymarket_price_changes(
    request: Request,
    window: str,
    max_lines: int = Query(default=500, ge=1, le=5000),
    auth: dict = Depends(get_current_user_from_api_key),
):
    """Best bid/ask price change events for a time window.

    Each row: server_ts_ms, condition_id, outcome, side (BUY/SELL), price, size, best_bid, best_ask.
    """
    require_scope(auth, "data:read")
    client = _get_polymarket_ob_client(request)
    data = await client.get_price_changes(window, max_lines)
    return {"window": window, "count": len(data), "data": data}


@router.get("/polymarket/{window}/trades")
async def polymarket_trades(
    request: Request,
    window: str,
    max_lines: int = Query(default=500, ge=1, le=5000),
    auth: dict = Depends(get_current_user_from_api_key),
):
    """Executed trades in a time window.

    Each row: server_ts_ms, condition_id, outcome, side, price, size, fee_rate_bps.
    """
    require_scope(auth, "data:read")
    client = _get_polymarket_ob_client(request)
    data = await client.get_trades(window, max_lines)
    return {"window": window, "count": len(data), "data": data}
