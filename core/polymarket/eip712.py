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


# Polymarket CTF Exchange contract on Polygon mainnet
_EXCHANGE_ADDRESS = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"

_EIP712_DOMAIN = {
    "name": "CTF Exchange",
    "version": "1",
}

_ORDER_TYPES = {
    "Order": [
        {"name": "salt", "type": "uint256"},
        {"name": "maker", "type": "address"},
        {"name": "signer", "type": "address"},
        {"name": "taker", "type": "address"},
        {"name": "tokenId", "type": "uint256"},
        {"name": "makerAmount", "type": "uint256"},
        {"name": "takerAmount", "type": "uint256"},
        {"name": "expiration", "type": "uint256"},
        {"name": "nonce", "type": "uint256"},
        {"name": "feeRateBps", "type": "uint256"},
        {"name": "side", "type": "uint8"},
        {"name": "signatureType", "type": "uint8"},
    ]
}


def sign_order_struct(order_struct: dict, private_key: str, chain_id: int = 137) -> dict:
    """
    Signs an EIP-712 order struct using the operator private key.
    Returns a new dict with the 'signature' field added (0x-prefixed hex).
    """
    from eth_account import Account

    domain = {
        **_EIP712_DOMAIN,
        "chainId": chain_id,
        "verifyingContract": _EXCHANGE_ADDRESS,
    }

    # EIP-712 typed data requires integer values (not strings)
    typed_data = {
        "salt": int(order_struct["salt"]) if isinstance(order_struct["salt"], str) else order_struct["salt"],
        "maker": order_struct["maker"],
        "signer": order_struct["signer"],
        "taker": order_struct["taker"],
        "tokenId": int(order_struct["tokenId"]) if isinstance(order_struct["tokenId"], str) else order_struct["tokenId"],
        "makerAmount": int(order_struct["makerAmount"]),
        "takerAmount": int(order_struct["takerAmount"]),
        "expiration": int(order_struct["expiration"]),
        "nonce": int(order_struct["nonce"]),
        "feeRateBps": int(order_struct["feeRateBps"]),
        "side": int(order_struct["side"]),
        "signatureType": int(order_struct["signatureType"]),
    }

    signed = Account.sign_typed_data(
        private_key,
        domain_data=domain,
        message_types=_ORDER_TYPES,
        message_data=typed_data,
    )
    sig_hex = signed.signature.hex()
    # Ensure 0x prefix exactly once
    if sig_hex.startswith("0x"):
        return {**order_struct, "signature": sig_hex}
    return {**order_struct, "signature": "0x" + sig_hex}
