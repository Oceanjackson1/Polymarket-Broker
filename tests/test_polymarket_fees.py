# tests/test_polymarket_fees.py
"""Tests for Polymarket platform fee calculation."""
import pytest
from core.polymarket_fees import (
    calc_taker_fee_rate,
    calc_taker_fee_bps,
    calc_taker_fee,
    calc_net_fee,
    resolve_category,
    estimate_trade_fees,
    CATEGORY_FEE_PARAMS,
)


class TestCalcTakerFeeRate:
    """Verify fee rates against official Polymarket fee table (from xlsx)."""

    @pytest.mark.parametrize("category,price,expected_rate", [
        # Crypto: feeRate=0.072, exponent=1
        ("crypto", 0.50, 0.0180),
        ("crypto", 0.80, 0.0115),
        ("crypto", 0.95, 0.0034),
        # Sports: feeRate=0.030, exponent=1
        ("sports", 0.50, 0.0075),
        ("sports", 0.80, 0.0048),
        ("sports", 0.95, 0.0014),  # rounded from 0.001425
        # Finance: feeRate=0.040, exponent=1
        ("finance", 0.50, 0.0100),
        ("finance", 0.80, 0.0064),
        ("finance", 0.95, 0.0019),
        # Politics: feeRate=0.040, exponent=1
        ("politics", 0.50, 0.0100),
        ("politics", 0.80, 0.0064),
        ("politics", 0.95, 0.0019),
        # Weather: feeRate=0.025, exponent=1
        ("weather", 0.50, 0.00625),
        ("weather", 0.80, 0.004),
        ("weather", 0.95, 0.001188),  # approx
        # Geopolitics: feeRate=0 — always free
        ("geopolitics", 0.50, 0.0),
        ("geopolitics", 0.95, 0.0),
        ("geopolitics", 0.10, 0.0),
    ])
    def test_fee_rates_match_xlsx(self, category, price, expected_rate):
        rate = calc_taker_fee_rate(category, price)
        assert abs(rate - expected_rate) < 0.001, (
            f"{category} @ p={price}: got {rate:.6f}, expected ~{expected_rate}"
        )

    def test_symmetric_around_half(self):
        """fee(p) == fee(1-p) because formula uses p*(1-p)."""
        for cat in ("crypto", "sports", "politics"):
            assert calc_taker_fee_rate(cat, 0.3) == pytest.approx(
                calc_taker_fee_rate(cat, 0.7), rel=1e-10
            )

    def test_max_at_p50(self):
        """p=0.50 gives maximum fee for any category."""
        for cat in CATEGORY_FEE_PARAMS:
            if cat == "geopolitics":
                continue
            rate_50 = calc_taker_fee_rate(cat, 0.50)
            rate_30 = calc_taker_fee_rate(cat, 0.30)
            rate_80 = calc_taker_fee_rate(cat, 0.80)
            assert rate_50 >= rate_30
            assert rate_50 >= rate_80

    def test_boundary_prices(self):
        rate_0 = calc_taker_fee_rate("crypto", 0.0)
        rate_1 = calc_taker_fee_rate("crypto", 1.0)
        assert rate_0 == 0.0
        assert rate_1 == 0.0

    def test_unknown_category_uses_other(self):
        rate = calc_taker_fee_rate("unknown_xyz", 0.50)
        other_rate = calc_taker_fee_rate("other", 0.50)
        assert rate == other_rate


class TestCalcTakerFeeBps:
    def test_crypto_p50(self):
        bps = calc_taker_fee_bps("crypto", 0.50)
        assert bps == 180  # 1.80%

    def test_geopolitics_always_zero(self):
        assert calc_taker_fee_bps("geopolitics", 0.50) == 0
        assert calc_taker_fee_bps("geopolitics", 0.95) == 0


class TestCalcTakerFee:
    def test_absolute_amount(self):
        fee = calc_taker_fee("crypto", 0.50, 1000)
        assert abs(fee - 18.0) < 0.01  # 1000 * 0.018

    def test_zero_volume(self):
        assert calc_taker_fee("crypto", 0.50, 0) == 0.0


class TestCalcNetFee:
    def test_net_fee_with_rebate(self):
        # Crypto: maker_rebate=0.20, poly_retention=0.80
        gross = calc_taker_fee("crypto", 0.50, 1000)  # 18.0
        net = calc_net_fee("crypto", 0.50, 1000)
        assert abs(net - gross * 0.80) < 0.01


class TestResolveCategory:
    def test_direct_match(self):
        assert resolve_category(["crypto"]) == "crypto"
        assert resolve_category(["sports"]) == "sports"
        assert resolve_category(["politics"]) == "politics"

    def test_alias_match(self):
        assert resolve_category(["bitcoin"]) == "crypto"
        assert resolve_category(["nba"]) == "sports"
        assert resolve_category(["election"]) == "politics"
        assert resolve_category(["temperature"]) == "weather"

    def test_case_insensitive(self):
        assert resolve_category(["CRYPTO"]) == "crypto"
        assert resolve_category(["Bitcoin"]) == "crypto"

    def test_first_known_tag_wins(self):
        assert resolve_category(["unknown", "crypto", "sports"]) == "crypto"

    def test_no_tags_returns_other(self):
        assert resolve_category(None) == "other"
        assert resolve_category([]) == "other"

    def test_unknown_tags_return_other(self):
        assert resolve_category(["some_random_tag"]) == "other"


class TestEstimateTradeFees:
    def test_structure(self):
        result = estimate_trade_fees("crypto", 0.95, 100, broker_fee_bps=10)
        assert "polymarket_fee_bps" in result
        assert "broker_fee_bps" in result
        assert "total_fee_amount" in result
        assert "net_profit_if_win" in result
        assert result["broker_fee_bps"] == 10

    def test_net_profit_accounts_for_fees(self):
        result = estimate_trade_fees("crypto", 0.95, 100, broker_fee_bps=10)
        assert result["net_profit_if_win"] < result["gross_profit_if_win"]

    def test_geopolitics_zero_poly_fee(self):
        result = estimate_trade_fees("geopolitics", 0.95, 100, broker_fee_bps=0)
        assert result["polymarket_fee_amount"] == 0
        assert result["polymarket_fee_bps"] == 0
