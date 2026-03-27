from __future__ import annotations
from typing import Any


async def handle_market_query(
    params: dict[str, Any],
    gamma_client: Any,
    dome_client: Any | None = None,
) -> dict:
    """Search or query markets. Actions: search, detail, orderbook."""
    action = params.get("action", "search")
    query = params.get("query", "")

    if action == "search":
        markets = await gamma_client.get_markets(query=query)
        return {
            "success": True,
            "markets": [
                {
                    "condition_id": m.get("condition_id", ""),
                    "question": m.get("question", ""),
                    "best_price": m["tokens"][0]["price"] if m.get("tokens") else None,
                }
                for m in (markets or [])[:10]
            ],
        }

    if action == "detail":
        market_id = params.get("market_id", "")
        market = await gamma_client.get_market(market_id)
        return {"success": True, "market": market}

    return {"success": False, "error": f"Unknown action: {action}"}
