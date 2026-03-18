from decimal import Decimal
from typing import Optional

_MAX_ORDER_USDC: dict[str, Optional[Decimal]] = {
    "free": Decimal("1000"),
    "pro": Decimal("50000"),
    "enterprise": None,  # unlimited
}

_MAX_POSITION_USDC: dict[str, Optional[Decimal]] = {
    "free": Decimal("5000"),
    "pro": None,  # unlimited
    "enterprise": None,  # unlimited
}


def validate_order_size(tier: str, size: float, price: float) -> None:
    """Raises ValueError if order notional exceeds tier limit. None means unlimited."""
    limit = _MAX_ORDER_USDC.get(tier.lower(), _MAX_ORDER_USDC["free"])
    if limit is None:
        return  # unlimited
    notional = Decimal(str(size)) * Decimal(str(price))
    if notional > limit:
        raise ValueError(f"ORDER_SIZE_EXCEEDED: max {limit} USDC for '{tier}' tier")


def check_position_cap(tier: str, existing_notional: float, new_notional: float) -> None:
    """Raises ValueError if adding new_notional to existing would exceed per-market cap."""
    cap = _MAX_POSITION_USDC.get(tier.lower(), _MAX_POSITION_USDC["free"])
    if cap is None:
        return  # unlimited
    total = Decimal(str(existing_notional)) + Decimal(str(new_notional))
    if total > cap:
        raise ValueError(
            f"POSITION_CAP_EXCEEDED: per-market cap is {cap} USDC for '{tier}' tier"
        )
