from __future__ import annotations
from typing import Any


async def handle_cancel_order(
    params: dict[str, Any],
    db_session: Any,
    user_id: str,
) -> dict:
    """Cancel a single order or all open orders."""
    from api.orders.service import OrderService

    svc = OrderService(db_session)
    cancel_all = params.get("cancel_all", False)

    if cancel_all:
        count = await svc.cancel_all_open(user_id=user_id, api_key="")
        return {
            "success": True,
            "_type": "cancel_result",
            "cancelled_count": count,
            "message": f"Cancelled {count} open order(s).",
        }

    order_id = params.get("order_id")
    if not order_id:
        return {"success": False, "error": "No order_id provided. Say 'cancel all' to cancel all open orders."}

    try:
        order = await svc.cancel_order(user_id=user_id, order_id=order_id, api_key="")
        return {
            "success": True,
            "_type": "cancel_result",
            "order_id": order.id,
            "status": order.status,
            "message": f"Order {order.id} cancelled.",
        }
    except KeyError:
        return {"success": False, "error": f"Order {order_id} not found."}
    except ValueError as e:
        return {"success": False, "error": str(e)}
