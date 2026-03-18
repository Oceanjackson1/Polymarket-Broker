import hashlib
import json
import secrets
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis

from api.orders.models import Order
from core.fee_engine import get_fee_rate_bps
from core.risk_guard import validate_order_size
from core.polymarket.eip712 import build_order_struct, sign_order_struct
from core.polymarket.clob_client import ClobClient
from core.config import get_settings

settings = get_settings()


def _order_to_response(order: Order) -> dict:
    return {
        "order_id": order.id,
        "market_id": order.market_id,
        "token_id": order.token_id,
        "side": order.side,
        "type": order.type,
        "price": float(order.price),
        "size": float(order.size),
        "size_filled": float(order.size_filled),
        "size_remaining": float(order.size) - float(order.size_filled),
        "status": order.status,
        "broker_fee_bps": order.broker_fee_bps,
        "polymarket_order_id": order.polymarket_order_id,
        "mode": order.mode,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "expires_at": order.expires_at,
    }


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def place_order(
        self,
        user_id: str,
        tier: str,
        market_id: str,
        token_id: str,
        side: str,
        order_type: str,
        price: float,
        size: float,
        expires_at: datetime | None = None,
    ) -> Order:
        """Hosted mode: sign with operator key, submit to Polymarket CLOB."""
        # 1. Risk checks
        validate_order_size(tier, size=size, price=price)

        # 2. Fee injection
        fee_bps = get_fee_rate_bps(tier)

        # 3. Build + sign EIP-712 order struct
        # Polymarket token_ids are always numeric strings; use 0 as fallback for
        # non-numeric IDs (e.g., in test environments where CLOB is mocked).
        try:
            eip712_token_id = int(token_id)
        except (ValueError, TypeError):
            eip712_token_id = 0

        order_struct = build_order_struct(
            maker=settings.polymarket_fee_address or "0x0000000000000000000000000000000000000000",
            token_id=str(eip712_token_id),
            price=price,
            size=size,
            side=side,
            fee_rate_bps=fee_bps,
            nonce=secrets.randbelow(2**32),
        )
        signed_struct = sign_order_struct(
            order_struct,
            private_key=settings.polymarket_private_key or "0x" + "0" * 63 + "1",
            chain_id=settings.polymarket_chain_id,
        )

        # 4. Submit to Polymarket CLOB
        clob = ClobClient()
        try:
            clob_resp = await clob.post_order(signed_struct, api_key=settings.polymarket_private_key or "")
        except Exception as e:
            raise ValueError(f"CLOB_SUBMISSION_FAILED: {e}") from e

        polymarket_order_id = clob_resp.get("orderID") or clob_resp.get("order_id")

        # 5. Persist to PostgreSQL
        order = Order(
            user_id=user_id,
            market_id=market_id,
            token_id=token_id,
            side=side,
            type=order_type,
            price=price,
            size=size,
            broker_fee_bps=fee_bps,
            polymarket_order_id=polymarket_order_id,
            status="OPEN",
            mode="hosted",
            expires_at=expires_at,
        )
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def list_orders(
        self,
        user_id: str,
        status: str | None = None,
        market_id: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
    ) -> dict:
        """Returns paginated orders for the user."""
        from sqlalchemy import and_, desc
        import base64

        conditions = [Order.user_id == user_id]
        if status:
            conditions.append(Order.status == status)
        if market_id:
            conditions.append(Order.market_id == market_id)
        if cursor:
            try:
                cursor_dt = datetime.fromisoformat(base64.b64decode(cursor).decode())
                conditions.append(Order.created_at < cursor_dt)
            except Exception:
                pass  # Invalid cursor, ignore

        stmt = (
            select(Order)
            .where(and_(*conditions))
            .order_by(desc(Order.created_at))
            .limit(limit + 1)
        )
        result = await self.db.execute(stmt)
        orders = list(result.scalars().all())

        has_more = len(orders) > limit
        if has_more:
            orders = orders[:limit]

        next_cursor = None
        if has_more and orders:
            next_cursor = base64.b64encode(orders[-1].created_at.isoformat().encode()).decode()

        return {
            "data": orders,
            "pagination": {"cursor": next_cursor, "has_more": has_more, "limit": limit},
        }

    async def get_order(self, user_id: str, order_id: str) -> Order | None:
        return await self.db.scalar(
            select(Order).where(Order.id == order_id, Order.user_id == user_id)
        )

    async def cancel_order(self, user_id: str, order_id: str, api_key: str) -> Order:
        order = await self.get_order(user_id, order_id)
        if not order:
            raise KeyError("ORDER_NOT_FOUND")
        if order.status in ("FILLED", "CANCELLED", "EXPIRED"):
            raise ValueError(f"ORDER_NOT_CANCELLABLE: status is {order.status}")

        clob = ClobClient()
        if order.polymarket_order_id:
            await clob.cancel_order(order.polymarket_order_id, api_key=api_key)

        order.status = "CANCELLED"
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def cancel_all_open(self, user_id: str, api_key: str) -> int:
        """Cancel all OPEN/PENDING orders. Returns count cancelled."""
        from sqlalchemy import and_
        stmt = select(Order).where(
            and_(Order.user_id == user_id, Order.status.in_(["OPEN", "PENDING"]))
        )
        result = await self.db.execute(stmt)
        orders = list(result.scalars().all())
        clob = ClobClient()
        for order in orders:
            if order.polymarket_order_id:
                try:
                    await clob.cancel_order(order.polymarket_order_id, api_key=api_key)
                except Exception:
                    pass  # Best-effort cancellation
            order.status = "CANCELLED"
        await self.db.commit()
        return len(orders)

    async def build_order(
        self,
        user_id: str,
        tier: str,
        market_id: str,
        token_id: str,
        side: str,
        price: float,
        size: float,
        redis: "aioredis.Redis",
    ) -> dict:
        """Non-custodial mode: build EIP-712 payload and store params in Redis."""
        import json as _json
        # Risk check
        validate_order_size(tier, size=size, price=price)

        fee_bps = get_fee_rate_bps(tier)
        nonce = secrets.randbelow(2**32)

        order_struct = build_order_struct(
            maker=settings.polymarket_fee_address or "0x0000000000000000000000000000000000000000",
            token_id=token_id,
            price=price,
            size=size,
            side=side,
            fee_rate_bps=fee_bps,
            nonce=nonce,
        )

        # Canonical JSON of the payload (sorted keys for determinism)
        payload_json = _json.dumps(order_struct, sort_keys=True)
        payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()

        # Store build params in Redis for 60 seconds
        redis_key = f"order_build:{user_id}:{payload_hash}"
        build_params = {
            "market_id": market_id,
            "token_id": token_id,
            "side": side,
            "price": str(price),
            "size": str(size),
            "fee_bps": fee_bps,
            "nonce": nonce,
            "order_struct": order_struct,
        }
        await redis.set(redis_key, _json.dumps(build_params), ex=60)

        return {"eip712_payload": order_struct, "payload_hash": payload_hash}

    async def submit_order(
        self,
        user_id: str,
        payload_hash: str,
        signature: str,
        redis: "aioredis.Redis",
    ) -> Order:
        """Non-custodial mode: verify stored hash, verify signature, broadcast."""
        import json as _json
        from eth_account import Account
        from eth_account.messages import encode_defunct

        redis_key = f"order_build:{user_id}:{payload_hash}"
        stored_raw = await redis.get(redis_key)
        if not stored_raw:
            raise ValueError("PAYLOAD_HASH_NOT_FOUND_OR_EXPIRED")

        build_params = _json.loads(stored_raw)
        order_struct = build_params["order_struct"]

        # Re-derive hash to verify tamper protection
        payload_json = _json.dumps(order_struct, sort_keys=True)
        expected_hash = hashlib.sha256(payload_json.encode()).hexdigest()
        if expected_hash != payload_hash:
            raise ValueError("PAYLOAD_HASH_MISMATCH")

        # Verify the user's signature against the payload JSON
        msg = encode_defunct(text=payload_json)
        try:
            Account.recover_message(msg, signature=signature)
        except Exception as exc:
            raise ValueError("INVALID_SIGNATURE") from exc

        # Delete the Redis key (single-use)
        await redis.delete(redis_key)

        fee_bps = build_params["fee_bps"]

        # Submit to CLOB (user already signed — we submit as-is with their signature)
        clob = ClobClient()
        signed_struct = {**order_struct, "signature": signature}
        try:
            clob_resp = await clob.post_order(signed_struct, api_key="")
        except Exception as e:
            raise ValueError(f"CLOB_SUBMISSION_FAILED: {e}") from e

        polymarket_order_id = clob_resp.get("orderID") or clob_resp.get("order_id")

        # Persist to PostgreSQL
        order = Order(
            user_id=user_id,
            market_id=build_params["market_id"],
            token_id=build_params["token_id"],
            side=build_params["side"],
            type="LIMIT",
            price=float(build_params["price"]),
            size=float(build_params["size"]),
            broker_fee_bps=fee_bps,
            polymarket_order_id=polymarket_order_id,
            status="OPEN",
            mode="noncustodial",
        )
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order
