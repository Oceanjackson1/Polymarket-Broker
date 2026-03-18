_TIER_FEE_RATE_BPS: dict[str, int] = {
    "free": 10,        # 0.10% broker layer
    "pro": 5,          # 0.05% broker layer
    "enterprise": 0,   # 0.00% (custom negotiated at contract level)
}


def get_fee_rate_bps(tier: str) -> int:
    """Returns the broker-layer feeRateBps for the given subscription tier."""
    return _TIER_FEE_RATE_BPS.get(tier.lower(), _TIER_FEE_RATE_BPS["free"])
