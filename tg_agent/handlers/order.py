from __future__ import annotations
from typing import Any


async def handle_place_order(
    params: dict[str, Any],
    db_session: Any,
    user_id: str,
) -> dict:
    """Place a hosted-mode order via OrderService."""
    from api.orders.service import OrderService

    svc = OrderService(db_session)
    order = await svc.place_order(
        user_id=user_id,
        token_id=params["token_id"],
        side=params["side"],
        price=params["price"],
        size=params["size"],
    )
    return {"success": True, "order_id": order.id, "status": order.status}
