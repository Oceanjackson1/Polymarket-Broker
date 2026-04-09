"""Strategy handler — convergence arbitrage scanning and position management."""
from __future__ import annotations
from datetime import datetime, UTC
from decimal import Decimal
from typing import Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession


CONVERGENCE_MIN_PROB = Decimal("0.95")
CONVERGENCE_MAX_DAYS = 3

STRATEGIES = [
    {
        "slug": "convergence",
        "name": "Convergence Arbitrage",
        "description": "Buy markets with prob >= 95% and expiry <= 3 days. Profit when market resolves to 1.00.",
        "min_tier": "pro",
    },
]


async def handle_strategy(
    params: dict[str, Any],
    db_session: AsyncSession,
    gamma_client: Any | None = None,
    user_id: str = "",
) -> dict:
    action = params.get("action", "scan")

    if action == "list":
        return {
            "success": True,
            "_type": "strategies",
            "data": STRATEGIES,
        }

    if action == "scan":
        return await _scan_convergence(gamma_client)

    if action == "positions":
        return await _get_convergence_positions(db_session, user_id)

    if action == "execute":
        return {
            "success": False,
            "error": "Use the confirmation buttons to execute convergence trades. This prevents accidental orders.",
        }

    return {"success": False, "error": f"Unknown strategy action: {action}"}


async def _scan_convergence(gamma_client: Any | None) -> dict:
    if not gamma_client:
        return {"success": False, "error": "Gamma client not available."}

    try:
        markets = await gamma_client.get_markets(limit=100, active=True, closed=False)
    except Exception as e:
        return {"success": False, "error": f"Failed to fetch markets: {e}"}

    now = datetime.now(UTC)
    opportunities = []

    for m in markets:
        raw_prices = m.get("outcomePrices", [])
        if isinstance(raw_prices, str):
            import json
            try:
                raw_prices = json.loads(raw_prices)
            except (json.JSONDecodeError, ValueError):
                continue
        if not raw_prices:
            continue

        price = Decimal(str(raw_prices[0]))
        if price < CONVERGENCE_MIN_PROB:
            continue

        end_date_str = m.get("endDate")
        if not end_date_str:
            continue
        try:
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
            days_to_expiry = (end_date - now).total_seconds() / 86400
            if days_to_expiry > CONVERGENCE_MAX_DAYS or days_to_expiry < 0:
                continue
        except (ValueError, TypeError):
            continue

        edge_bps = int((Decimal("1.0") - price) * 10000)

        opportunities.append({
            "market_id": m["id"],
            "question": m.get("question", ""),
            "current_price": float(price),
            "edge_bps": edge_bps,
            "days_to_expiry": round(days_to_expiry, 1),
            "volume": float(m.get("volume", 0) or 0),
        })

    opportunities.sort(key=lambda o: o["edge_bps"], reverse=True)
    return {
        "success": True,
        "_type": "convergence_opportunities",
        "data": opportunities[:20],
    }


async def _get_convergence_positions(db: AsyncSession, user_id: str) -> dict:
    from api.orders.models import Order

    result = await db.execute(
        select(Order)
        .where(
            Order.user_id == user_id,
            Order.price >= Decimal("0.95"),
            Order.status.in_(["OPEN", "PARTIALLY_FILLED", "FILLED"]),
        )
        .order_by(desc(Order.created_at))
        .limit(50)
    )
    orders = list(result.scalars().all())
    return {
        "success": True,
        "_type": "convergence_positions",
        "data": [
            {
                "order_id": o.id,
                "market_id": o.market_id,
                "side": o.side,
                "entry_price": float(o.price),
                "size": float(o.size),
                "status": o.status,
                "created_at": o.created_at.isoformat(),
            }
            for o in orders
        ],
    }
