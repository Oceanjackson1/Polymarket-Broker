from __future__ import annotations
from typing import Any


async def handle_portfolio(
    params: dict[str, Any],
    db_session: Any,
    user_id: str,
) -> dict:
    """Get user portfolio positions and P&L."""
    from api.portfolio.service import PortfolioService

    svc = PortfolioService(db_session)
    action = params.get("action", "positions")

    if action == "positions":
        positions = await svc.get_positions(user_id)
        return {"success": True, "positions": positions}

    if action == "balance":
        balance = await svc.get_balance(user_id)
        return {"success": True, "balance": balance}

    return {"success": False, "error": f"Unknown action: {action}"}
