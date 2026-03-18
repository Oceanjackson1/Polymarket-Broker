from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from db.postgres import get_session
from db.redis_client import get_redis
from api.deps import get_current_user_id, get_current_user_from_api_key
from api.orders.service import OrderService
from api.orders.schemas import (
    OrderRequest, OrderResponse, PaginatedOrders,
    BuildOrderRequest, BuildOrderResponse, SubmitOrderRequest,
)
from core.config import get_settings

settings = get_settings()


router = APIRouter(prefix="/orders", tags=["orders"])


def _order_to_response_dict(order) -> dict:
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


@router.post("", response_model=OrderResponse, status_code=201)
async def place_order(
    body: OrderRequest,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Hosted mode: sign with operator key and submit to Polymarket."""
    order = await OrderService(db).place_order(
        user_id=auth["user_id"],
        tier=auth["tier"],
        market_id=body.market_id,
        token_id=body.token_id,
        side=body.side,
        order_type=body.type,
        price=body.price,
        size=body.size,
        expires_at=body.expires_at,
    )
    return OrderResponse(**_order_to_response_dict(order))


@router.post("/build", response_model=BuildOrderResponse)
async def build_order(
    body: BuildOrderRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Non-custodial mode: build EIP-712 payload for user to sign."""
    from api.auth.models import User
    from sqlalchemy import select
    user = await db.scalar(select(User).where(User.id == user_id))
    tier = user.tier if user else "free"
    return await OrderService(db).build_order(
        user_id=user_id, tier=tier,
        market_id=body.market_id, token_id=body.token_id,
        side=body.side, price=body.price, size=body.size,
        redis=redis,
    )


@router.post("/submit", response_model=OrderResponse)
async def submit_order(
    body: SubmitOrderRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Non-custodial mode: submit signed EIP-712 order."""
    order = await OrderService(db).submit_order(
        user_id=user_id,
        payload_hash=body.payload_hash,
        signature=body.signature,
        redis=redis,
    )
    return OrderResponse(**_order_to_response_dict(order))


@router.get("", response_model=PaginatedOrders)
async def list_orders(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
    status: str | None = Query(default=None),
    market_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
):
    result = await OrderService(db).list_orders(
        user_id=auth["user_id"], status=status, market_id=market_id,
        limit=limit, cursor=cursor,
    )
    orders_resp = [OrderResponse(**_order_to_response_dict(o)) for o in result["data"]]
    return PaginatedOrders(data=orders_resp, pagination=result["pagination"])


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    order = await OrderService(db).get_order(user_id=auth["user_id"], order_id=order_id)
    if not order:
        raise HTTPException(404, detail="ORDER_NOT_FOUND")
    return OrderResponse(**_order_to_response_dict(order))


@router.delete("/{order_id}", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    order = await OrderService(db).cancel_order(
        user_id=auth["user_id"], order_id=order_id,
        api_key=settings.polymarket_api_key,
    )
    return OrderResponse(**_order_to_response_dict(order))


@router.delete("", status_code=200)
async def cancel_all_orders(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    count = await OrderService(db).cancel_all_open(
        user_id=auth["user_id"], api_key=settings.polymarket_api_key
    )
    return {"cancelled": count}
