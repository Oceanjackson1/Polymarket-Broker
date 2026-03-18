from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from api.orders.models import Order
from core.polymarket.clob_client import ClobClient


class PortfolioService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_positions(self, user_id: str) -> list[dict]:
        """Aggregate open/partially-filled orders into positions."""
        stmt = select(Order).where(
            and_(
                Order.user_id == user_id,
                Order.status.in_(["OPEN", "PARTIALLY_FILLED"]),
                Order.size_filled > 0,
            )
        )
        result = await self.db.execute(stmt)
        orders = list(result.scalars().all())

        # Group by market_id + token_id
        positions: dict[str, dict] = {}
        for order in orders:
            key = f"{order.market_id}:{order.token_id}"
            if key not in positions:
                positions[key] = {
                    "market_id": order.market_id,
                    "token_id": order.token_id,
                    "side": order.side,
                    "total_size_filled": 0.0,
                    "total_notional": 0.0,
                    "order_count": 0,
                }
            p = positions[key]
            filled = float(order.size_filled)
            p["total_size_filled"] += filled
            p["total_notional"] += filled * float(order.price)
            p["order_count"] += 1

        result_list = []
        for p in positions.values():
            avg_price = (p["total_notional"] / p["total_size_filled"]) if p["total_size_filled"] > 0 else 0.0
            result_list.append({
                "market_id": p["market_id"],
                "token_id": p["token_id"],
                "side": p["side"],
                "size_held": p["total_size_filled"],
                "avg_price": avg_price,
                "notional": p["total_notional"],
                "order_count": p["order_count"],
            })
        return result_list

    async def get_balance(self, user_id: str) -> dict:
        """USDC balance: real balance from CLOB (best-effort) + locked in open orders."""
        stmt = select(Order).where(
            and_(Order.user_id == user_id, Order.status.in_(["OPEN", "PENDING"]))
        )
        result = await self.db.execute(stmt)
        open_orders = list(result.scalars().all())
        locked = sum(
            float(o.price) * (float(o.size) - float(o.size_filled))
            for o in open_orders
        )

        balance = 0.0
        try:
            clob = ClobClient()
            bal_resp = await clob._get("/balance")
            balance = float(bal_resp.get("balance", 0))
        except Exception:
            pass  # Return 0 if CLOB unavailable

        return {
            "balance": balance,
            "locked": locked,
            "available": max(0.0, balance - locked),
        }

    async def get_pnl(self, user_id: str) -> dict:
        """Compute P&L from filled orders in our DB."""
        stmt = select(Order).where(
            and_(Order.user_id == user_id, Order.size_filled > 0)
        )
        result = await self.db.execute(stmt)
        orders = list(result.scalars().all())

        fees_paid_broker = sum(
            float(o.size_filled) * float(o.price) * (o.broker_fee_bps / 10000)
            for o in orders
        )

        buy_notional = sum(
            float(o.size_filled) * float(o.price)
            for o in orders if o.side == "BUY"
        )
        sell_notional = sum(
            float(o.size_filled) * float(o.price)
            for o in orders if o.side == "SELL"
        )
        realized = sell_notional - buy_notional

        return {
            "realized": realized,
            "unrealized": 0.0,   # Requires live price feed — Plan 3
            "fees_paid_broker": fees_paid_broker,
            "fees_paid_polymarket": 0.0,  # Requires on-chain query — Plan 3
        }
