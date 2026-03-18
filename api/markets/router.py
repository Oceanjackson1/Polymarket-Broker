from fastapi import APIRouter, Query, HTTPException
from core.polymarket.gamma_client import GammaClient
from core.polymarket.clob_client import ClobClient

router = APIRouter(prefix="/markets", tags=["markets"])

# Module-level client instances (mocked in tests via patch)
gamma_client = GammaClient()
clob_client = ClobClient()


@router.get("")
async def list_markets(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    """List all Polymarket markets with optional filters."""
    filters = {}
    if category:
        filters["category"] = category
    if status:
        filters["active"] = status == "active"
    try:
        markets = await gamma_client.get_markets(limit=limit, offset=offset, **filters)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")
    return {
        "data": markets,
        "pagination": {"limit": limit, "offset": offset, "has_more": len(markets) == limit},
    }


@router.get("/search")
async def search_markets(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Full-text search across market questions."""
    try:
        results = await gamma_client.get_markets(limit=limit, offset=offset, tag=q)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")
    return {
        "data": results,
        "pagination": {"limit": limit, "offset": offset, "has_more": len(results) == limit},
    }


@router.get("/{market_id}")
async def get_market(market_id: str):
    """Get a specific market by ID."""
    try:
        return await gamma_client.get_market(market_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")


@router.get("/{market_id}/orderbook")
async def get_orderbook(market_id: str, token_id: str = Query(...)):
    """Get the live order book for a market token."""
    try:
        return await clob_client.get_orderbook(token_id=token_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")


@router.get("/{market_id}/trades")
async def get_trades(
    market_id: str,
    limit: int = Query(default=20, ge=1, le=100),
):
    """Get recent trades for a market."""
    try:
        return await clob_client.get_trades(market_id=market_id, limit=limit)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")


@router.get("/{market_id}/midpoint")
async def get_midpoint(market_id: str, token_id: str = Query(...)):
    """Get the current mid price for a market token."""
    try:
        return await clob_client.get_midpoint(token_id=token_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")
