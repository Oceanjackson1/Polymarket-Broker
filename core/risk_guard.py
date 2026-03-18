from decimal import Decimal

_MAX_ORDER_USDC: dict[str, Decimal] = {
    "free": Decimal("1000"),
    "pro": Decimal("50000"),
    "enterprise": Decimal("999999999"),
}

_MAX_POSITION_USDC: dict[str, Decimal] = {
    "free": Decimal("5000"),
    "pro": Decimal("999999999"),
    "enterprise": Decimal("999999999"),
}


def validate_order_size(tier: str, size: float, price: float) -> None:
    """Raises ValueError if order notional exceeds tier limit."""
    notional = Decimal(str(size)) * Decimal(str(price))
    limit = _MAX_ORDER_USDC.get(tier.lower(), _MAX_ORDER_USDC["free"])
    if notional > limit:
        raise ValueError(f"ORDER_SIZE_EXCEEDED: max {limit} USDC for '{tier}' tier")


def check_position_cap(tier: str, existing_notional: float, new_notional: float) -> None:
    """Raises ValueError if adding new_notional to existing_notional would exceed per-market cap."""
    cap = _MAX_POSITION_USDC.get(tier.lower(), _MAX_POSITION_USDC["free"])
    total = Decimal(str(existing_notional)) + Decimal(str(new_notional))
    if total > cap:
        raise ValueError(
            f"POSITION_CAP_EXCEEDED: per-market cap is {cap} USDC for '{tier}' tier"
        )
