# api/strategies/router.py
"""Strategies API — v1 ships with convergence arbitrage only."""
from datetime import datetime, UTC
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from db.postgres import get_session
from api.deps import get_current_user_from_api_key, require_scope
from api.strategies.schemas import (
    StrategyInfo, ConvergenceOpportunity, ConvergenceExecuteRequest,
    ConvergenceExecuteResponse, ConvergencePosition,
)
from api.orders.models import Order
from core.polymarket.gamma_client import GammaClient
from core.polymarket_fees import resolve_category, calc_taker_fee_bps
from core.fee_engine import get_fee_rate_bps

router = APIRouter(prefix="/strategies", tags=["strategies"])

STRATEGIES = [
    StrategyInfo(
        slug="convergence",
        name="Convergence Arbitrage",
        description="Buy markets with prob >= 95% and expiry <= 3 days. Profit when market resolves to 1.00.",
        min_tier="pro",
    ),
]

CONVERGENCE_MIN_PROB = Decimal("0.95")
CONVERGENCE_MAX_DAYS = 3


@router.get("", response_model=list[StrategyInfo])
async def list_strategies(
    auth: dict = Depends(get_current_user_from_api_key),
):
    """List available strategy slugs with metadata."""
    require_scope(auth, "strategies:execute")
    return STRATEGIES


@router.get("/convergence/opportunities", response_model=list[ConvergenceOpportunity])
async def get_convergence_opportunities(
    auth: dict = Depends(get_current_user_from_api_key),
):
    """Markets with prob >= 95% and expiry <= 3 days — convergence candidates."""
    require_scope(auth, "strategies:execute")

    tier = auth.get("tier", "free")
    if tier not in ("pro", "enterprise"):
        raise HTTPException(403, detail="STRATEGY_REQUIRES_PRO_TIER")

    gamma = GammaClient()
    try:
        markets = await gamma.get_markets(limit=100, active=True, closed=False)
    finally:
        await gamma.close()

    now = datetime.now(UTC)
    opportunities = []

    for m in markets:
        raw_prices = m.get("outcomePrices", [])
        if isinstance(raw_prices, str):
            import json
            try:
                raw_prices = json.loads(raw_prices)
            except (json.JSONDecodeError, ValueError):
                raw_prices = []
        if not raw_prices:
            continue
        price = Decimal(str(raw_prices[0]))
        if price < CONVERGENCE_MIN_PROB:
            continue

        end_date_str = m.get("endDate")
        end_date = None
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                days_to_expiry = (end_date - now).total_seconds() / 86400
                if days_to_expiry > CONVERGENCE_MAX_DAYS or days_to_expiry < 0:
                    continue
            except (ValueError, TypeError):
                continue
        else:
            continue

        edge_bps = int((Decimal("1.0") - price) * 10000)

        # Fee-adjusted edge
        tags = m.get("tags", [])
        category = resolve_category(tags)
        poly_fee_bps = calc_taker_fee_bps(category, float(price))
        broker_bps = get_fee_rate_bps(tier)
        adjusted_edge = edge_bps - poly_fee_bps - broker_bps

        opportunities.append(ConvergenceOpportunity(
            market_id=m["id"],
            question=m.get("question", ""),
            current_price=price,
            estimated_true_prob=Decimal("1.0"),
            edge_bps=edge_bps,
            category=category,
            polymarket_fee_bps=poly_fee_bps,
            adjusted_edge_bps=adjusted_edge,
            expiry=end_date,
            volume=Decimal(str(m.get("volume", 0) or 0)),
        ))

    opportunities.sort(key=lambda o: o.edge_bps, reverse=True)
    return opportunities[:20]


@router.post("/convergence/execute", response_model=ConvergenceExecuteResponse)
async def execute_convergence(
    body: ConvergenceExecuteRequest,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Place a convergence trade — delegates to the order service."""
    require_scope(auth, "strategies:execute")

    tier = auth.get("tier", "free")
    if tier not in ("pro", "enterprise"):
        raise HTTPException(403, detail="STRATEGY_REQUIRES_PRO_TIER")

    from api.orders.service import OrderService
    import redis.asyncio as aioredis
    from db.redis_client import get_redis_pool

    redis = await get_redis_pool()
    svc = OrderService(db, redis)

    try:
        order = await svc.place_order(
            user_id=auth["user_id"],
            market_id=body.market_id,
            token_id=body.token_id,
            side=body.side,
            price=float(body.size),  # convergence buys at market
            size=float(body.size),
            order_type="LIMIT",
            tier=auth.get("tier", "free"),
        )
    except Exception as e:
        raise HTTPException(400, detail=f"ORDER_FAILED: {e}")

    return ConvergenceExecuteResponse(
        order_id=order.id,
        market_id=body.market_id,
        side=body.side,
        price=order.price,
        size=order.size,
        strategy="convergence",
        status=order.status,
        executed_at=datetime.now(UTC),
    )


@router.get("/convergence/positions", response_model=list[ConvergencePosition])
async def get_convergence_positions(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Active convergence positions (orders placed via this strategy)."""
    require_scope(auth, "strategies:execute")

    # For v1, convergence positions are just orders with high entry prices (>= 0.95)
    result = await db.execute(
        select(Order)
        .where(
            Order.user_id == auth["user_id"],
            Order.price >= Decimal("0.95"),
            Order.status.in_(["OPEN", "PARTIALLY_FILLED", "FILLED"]),
        )
        .order_by(desc(Order.created_at))
        .limit(50)
    )
    orders = list(result.scalars().all())

    return [
        ConvergencePosition(
            order_id=o.id,
            market_id=o.market_id,
            question=None,
            side=o.side,
            entry_price=o.price,
            size=o.size,
            current_price=None,
            unrealized_pnl=None,
            status=o.status,
            opened_at=o.created_at,
        )
        for o in orders
    ]
