# api/fees/router.py
"""Fee schedule and real-time fee estimation endpoints."""
from fastapi import APIRouter, Query

from core.polymarket_fees import (
    CATEGORY_FEE_PARAMS,
    calc_taker_fee_rate,
    resolve_category,
)
from core.fee_engine import get_fee_rate_bps, get_total_fee_estimate
from api.fees.schemas import (
    CategoryFeeInfo,
    FeeScheduleResponse,
    FeeEstimateResponse,
    MarketFeeResponse,
)

router = APIRouter(prefix="/fees", tags=["fees"])

_FORMULA = "fee = volume × feeRate × (p × (1-p))^exponent"


@router.get("/schedule", response_model=FeeScheduleResponse)
async def fee_schedule():
    """All category fee parameters with sample rates at key price points."""
    categories = []
    for name, params in CATEGORY_FEE_PARAMS.items():
        categories.append(CategoryFeeInfo(
            category=name,
            fee_rate=params.fee_rate,
            exponent=params.exponent,
            maker_rebate=params.maker_rebate,
            poly_retention=params.poly_retention,
            fee_at_p50=round(calc_taker_fee_rate(name, 0.50), 6),
            fee_at_p80=round(calc_taker_fee_rate(name, 0.80), 6),
            fee_at_p95=round(calc_taker_fee_rate(name, 0.95), 6),
        ))
    return FeeScheduleResponse(formula=_FORMULA, categories=categories)


@router.get("/estimate", response_model=FeeEstimateResponse)
async def fee_estimate(
    category: str = Query(..., description="Market category (crypto, sports, politics, etc.)"),
    price: float = Query(..., gt=0, lt=1, description="Outcome probability / price (0-1)"),
    volume: float = Query(default=100.0, gt=0, description="Trade volume in USDC"),
    tier: str = Query(default="free", description="User tier (free, pro, enterprise)"),
):
    """Real-time fee estimate for a given category, price, and volume."""
    result = get_total_fee_estimate(tier, category.lower(), price, volume)
    return FeeEstimateResponse(**result)


@router.get("/market/{token_id}", response_model=MarketFeeResponse)
async def market_fee(
    token_id: str,
    volume: float = Query(default=100.0, gt=0),
    tier: str = Query(default="free"),
):
    """Look up a market's fee by token_id: auto-detect category + fetch midpoint."""
    from core.polymarket.gamma_client import GammaClient
    from core.polymarket.clob_client import ClobClient

    # Fetch market metadata to get tags
    gamma = GammaClient()
    question = None
    category = "other"
    try:
        markets = await gamma.get_markets(limit=10, active=True)
        for m in markets:
            tokens = m.get("clobTokenIds", [])
            if token_id in tokens:
                tags = m.get("tags", [])
                category = resolve_category(tags)
                question = m.get("question")
                break
    finally:
        await gamma.close()

    # Fetch midpoint price
    midpoint = None
    try:
        clob = ClobClient()
        mid_resp = await clob.get_midpoint(token_id)
        midpoint = float(mid_resp.get("mid", 0)) if mid_resp else None
    except Exception:
        pass

    fee_est = None
    if midpoint and 0 < midpoint < 1:
        result = get_total_fee_estimate(tier, category, midpoint, volume)
        fee_est = FeeEstimateResponse(**result)

    return MarketFeeResponse(
        token_id=token_id,
        market_question=question,
        detected_category=category,
        midpoint_price=midpoint,
        fee_estimate=fee_est,
    )
