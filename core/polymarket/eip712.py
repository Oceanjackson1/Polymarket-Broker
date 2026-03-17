"""
EIP-712 order struct builder for Polymarket CLOB.
"""
from decimal import Decimal

USDC_DECIMALS = 6


def to_units(value: float) -> int:
    """Convert float to USDC contract units (6 decimals)."""
    return int(Decimal(str(value)) * Decimal(10 ** USDC_DECIMALS))


def build_order_struct(
    maker: str,
    token_id: str,
    price: float,
    size: float,
    side: str,          # "BUY" or "SELL"
    fee_rate_bps: int,
    nonce: int = 0,
    expiration: int = 0,
) -> dict:
    """
    Builds the unsigned EIP-712 order dict.
    BUY:  makerAmount = size * price (USDC spent), takerAmount = size (tokens received)
    SELL: makerAmount = size (tokens spent),        takerAmount = size * price (USDC received)
    """
    if side == "BUY":
        maker_amount = to_units(size * price)
        taker_amount = to_units(size)
    else:
        maker_amount = to_units(size)
        taker_amount = to_units(size * price)

    return {
        "salt": nonce,
        "maker": maker,
        "signer": maker,
        "taker": "0x0000000000000000000000000000000000000000",
        "tokenId": token_id,
        "makerAmount": str(maker_amount),
        "takerAmount": str(taker_amount),
        "expiration": str(expiration),
        "nonce": str(nonce),
        "feeRateBps": str(fee_rate_bps),
        "side": 0 if side == "BUY" else 1,
        "signatureType": 0,
    }
