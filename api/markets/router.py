import logging
from fastapi import APIRouter, Query, HTTPException, Request
from core.polymarket.gamma_client import GammaClient
from core.polymarket.clob_client import ClobClient
from core.dome.client import extract_list

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/markets", tags=["markets"])

# Module-level client instances (mocked in tests via patch)
gamma_client = GammaClient()
clob_client = ClobClient()


def _get_dome(request: Request):
    """Get DomeClient from app.state, or None if not configured."""
    return getattr(request.app.state, "dome_client", None)


@router.get("")
async def list_markets(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    """List Polymarket markets. Primary: Dome API, fallback: Gamma."""
    dome = _get_dome(request)
    if dome:
        try:
            resp = await dome.get_markets(
                tags=[category] if category else None,
                status="open" if status == "active" else status,
                limit=limit,
            )
            markets = extract_list(resp)
            return {
                "data": markets,
                "pagination": {"limit": limit, "offset": offset, "has_more": len(markets) == limit},
            }
        except Exception:
            logger.debug("dome list_markets failed, falling back to gamma")

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
    request: Request,
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Full-text search. Primary: Dome API, fallback: Gamma."""
    dome = _get_dome(request)
    if dome:
        try:
            resp = await dome.get_markets(search=q, limit=limit)
            results = extract_list(resp)
            return {
                "data": results,
                "pagination": {"limit": limit, "offset": offset, "has_more": len(results) == limit},
            }
        except Exception:
            logger.debug("dome search failed, falling back to gamma")

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
async def get_orderbook(request: Request, market_id: str, token_id: str = Query(...)):
    """Get the live order book. Primary: Dome snapshots, fallback: CLOB."""
    dome = _get_dome(request)
    if dome:
        try:
            resp = await dome.get_orderbook_snapshots(token_id, limit=1)
            snapshots = extract_list(resp)
            if snapshots:
                return snapshots[0]
        except Exception:
            logger.debug("dome orderbook failed, falling back to clob")

    try:
        return await clob_client.get_orderbook(token_id=token_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")


@router.get("/{market_id}/trades")
async def get_trades(
    request: Request,
    market_id: str,
    limit: int = Query(default=20, ge=1, le=100),
):
    """Get recent trades. Primary: Dome, fallback: CLOB."""
    dome = _get_dome(request)
    if dome:
        try:
            resp = await dome.get_orders(condition_id=market_id, limit=limit)
            trades = extract_list(resp)
            if trades:
                return trades
        except Exception:
            logger.debug("dome trades failed, falling back to clob")

    try:
        return await clob_client.get_trades(market_id=market_id, limit=limit)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")


@router.get("/{market_id}/midpoint")
async def get_midpoint(request: Request, market_id: str, token_id: str = Query(...)):
    """Get the current mid price. Primary: Dome price, fallback: CLOB."""
    dome = _get_dome(request)
    if dome:
        try:
            return await dome.get_market_price(token_id)
        except Exception:
            logger.debug("dome midpoint failed, falling back to clob")

    try:
        return await clob_client.get_midpoint(token_id=token_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")
