from core.polymarket_fees import (
    calc_taker_fee_rate,
    calc_taker_fee_bps,
    estimate_trade_fees,
    resolve_category,
)

_TIER_FEE_RATE_BPS: dict[str, int] = {
    "free": 10,        # 0.10% broker layer
    "pro": 5,          # 0.05% broker layer
    "enterprise": 0,   # 0.00% (custom negotiated at contract level)
}


def get_fee_rate_bps(tier: str) -> int:
    """Returns the broker-layer feeRateBps for the given subscription tier."""
    return _TIER_FEE_RATE_BPS.get(tier.lower(), _TIER_FEE_RATE_BPS["free"])


def get_total_fee_estimate(
    tier: str,
    category: str,
    price: float,
    volume: float,
) -> dict:
    """Combined broker + Polymarket platform fee estimate for a trade."""
    broker_bps = get_fee_rate_bps(tier)
    return estimate_trade_fees(category, price, volume, broker_fee_bps=broker_bps)
