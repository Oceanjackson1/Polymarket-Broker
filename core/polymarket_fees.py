# core/polymarket_fees.py
"""Polymarket platform fee calculation based on official fee formula.

fee = volume × feeRate × (p × (1-p))^exponent
net_fee = fee × (1 - makerRebate)

Fee parameters differ by market category. Prices near 0.50 pay the highest
fees; prices near 0 or 1 approach zero fees.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CategoryFeeParams:
    fee_rate: float
    exponent: int
    maker_rebate: float  # fraction returned to maker (0.0–1.0)

    @property
    def poly_retention(self) -> float:
        return 1.0 - self.maker_rebate


# ─── Official Polymarket fee schedule (2025-Q1 update) ────────────────────────

CATEGORY_FEE_PARAMS: dict[str, CategoryFeeParams] = {
    "crypto":      CategoryFeeParams(fee_rate=0.072, exponent=1, maker_rebate=0.20),
    "sports":      CategoryFeeParams(fee_rate=0.030, exponent=1, maker_rebate=0.25),
    "finance":     CategoryFeeParams(fee_rate=0.040, exponent=1, maker_rebate=0.50),
    "politics":    CategoryFeeParams(fee_rate=0.040, exponent=1, maker_rebate=0.25),
    "economics":   CategoryFeeParams(fee_rate=0.030, exponent=1, maker_rebate=0.25),
    "culture":     CategoryFeeParams(fee_rate=0.050, exponent=1, maker_rebate=0.25),
    "weather":     CategoryFeeParams(fee_rate=0.025, exponent=1, maker_rebate=0.25),
    "tech":        CategoryFeeParams(fee_rate=0.040, exponent=1, maker_rebate=0.25),
    "other":       CategoryFeeParams(fee_rate=0.200, exponent=2, maker_rebate=0.25),
    "mentions":    CategoryFeeParams(fee_rate=0.250, exponent=2, maker_rebate=0.25),
    "geopolitics": CategoryFeeParams(fee_rate=0.000, exponent=1, maker_rebate=0.00),
}

# Tag aliases → canonical category name
_TAG_TO_CATEGORY: dict[str, str] = {
    "crypto": "crypto", "bitcoin": "crypto", "ethereum": "crypto",
    "defi": "crypto", "btc": "crypto", "eth": "crypto",
    "sports": "sports", "nba": "sports", "nfl": "sports",
    "mlb": "sports", "soccer": "sports", "mma": "sports",
    "tennis": "sports", "golf": "sports", "hockey": "sports",
    "finance": "finance", "stocks": "finance", "bonds": "finance",
    "fed": "finance", "interest-rates": "finance",
    "politics": "politics", "election": "politics", "elections": "politics",
    "economics": "economics", "gdp": "economics", "inflation": "economics",
    "jobs": "economics", "cpi": "economics",
    "culture": "culture", "entertainment": "culture", "awards": "culture",
    "tv": "culture", "movies": "culture", "music": "culture",
    "weather": "weather", "temperature": "weather", "climate": "weather",
    "tech": "tech", "technology": "tech", "ai": "tech", "apple": "tech",
    "google": "tech", "science": "tech",
    "mentions": "mentions", "social-media": "mentions",
    "geopolitics": "geopolitics", "war": "geopolitics", "conflict": "geopolitics",
}


def resolve_category(tags: list[str] | None) -> str:
    """Map market tags to the canonical fee category. Falls back to 'other'."""
    if not tags:
        return "other"
    for tag in tags:
        cat = _TAG_TO_CATEGORY.get(tag.lower().strip())
        if cat:
            return cat
    return "other"


def calc_taker_fee_rate(category: str, price: float) -> float:
    """Per-$1 taker fee rate for a category at a given price.

    Returns feeRate × (p × (1-p))^exponent.
    """
    params = CATEGORY_FEE_PARAMS.get(category.lower(), CATEGORY_FEE_PARAMS["other"])
    if params.fee_rate == 0:
        return 0.0
    p = max(0.0, min(1.0, price))
    return params.fee_rate * (p * (1 - p)) ** params.exponent


def calc_taker_fee(category: str, price: float, volume: float) -> float:
    """Absolute taker fee amount for a trade."""
    return volume * calc_taker_fee_rate(category, price)


def calc_net_fee(category: str, price: float, volume: float) -> float:
    """Net fee retained by Polymarket (after maker rebate)."""
    params = CATEGORY_FEE_PARAMS.get(category.lower(), CATEGORY_FEE_PARAMS["other"])
    gross = calc_taker_fee(category, price, volume)
    return gross * params.poly_retention


def calc_taker_fee_bps(category: str, price: float) -> int:
    """Taker fee rate expressed in basis points (rounded)."""
    return round(calc_taker_fee_rate(category, price) * 10_000)


def estimate_trade_fees(
    category: str,
    price: float,
    volume: float,
    broker_fee_bps: int = 0,
) -> dict:
    """Full fee breakdown for a prospective trade.

    Returns dict with all fee components useful for display and decision-making.
    """
    poly_fee_rate = calc_taker_fee_rate(category, price)
    poly_fee_bps = round(poly_fee_rate * 10_000)
    poly_fee_amount = volume * poly_fee_rate
    broker_fee_amount = volume * (broker_fee_bps / 10_000)
    total_fee = poly_fee_amount + broker_fee_amount

    # For a BUY at price p: shares = volume / p, payout if win = shares × 1.0
    # gross_profit = payout - volume = volume × (1/p - 1) = volume × (1-p)/p
    if price > 0:
        gross_profit = volume * (1 - price) / price
    else:
        gross_profit = 0.0
    net_profit = gross_profit - total_fee

    return {
        "category": category,
        "price": price,
        "volume": volume,
        "polymarket_fee_rate": round(poly_fee_rate, 6),
        "polymarket_fee_bps": poly_fee_bps,
        "polymarket_fee_amount": round(poly_fee_amount, 6),
        "broker_fee_bps": broker_fee_bps,
        "broker_fee_amount": round(broker_fee_amount, 6),
        "total_fee_amount": round(total_fee, 6),
        "total_fee_bps": poly_fee_bps + broker_fee_bps,
        "gross_profit_if_win": round(gross_profit, 6),
        "net_profit_if_win": round(net_profit, 6),
    }
