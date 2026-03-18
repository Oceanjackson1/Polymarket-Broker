from core.fee_engine import get_fee_rate_bps


def test_free_tier_is_10_bps():
    assert get_fee_rate_bps("free") == 10


def test_pro_tier_is_5_bps():
    assert get_fee_rate_bps("pro") == 5


def test_enterprise_tier_is_0_bps():
    assert get_fee_rate_bps("enterprise") == 0


def test_unknown_tier_defaults_to_free():
    assert get_fee_rate_bps("unknown_tier") == 10
