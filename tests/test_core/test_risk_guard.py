import pytest
from core.risk_guard import validate_order_size, check_position_cap


def test_free_tier_allows_small_order():
    validate_order_size("free", size=100.0, price=0.65)  # 65 USDC, under 1000 limit


def test_free_tier_rejects_large_order():
    with pytest.raises(ValueError, match="ORDER_SIZE_EXCEEDED"):
        validate_order_size("free", size=2000.0, price=0.65)  # 1300 USDC, over 1000


def test_pro_tier_allows_large_order():
    validate_order_size("pro", size=10000.0, price=0.9)  # 9000 USDC, under 50000


def test_free_tier_position_cap():
    with pytest.raises(ValueError, match="POSITION_CAP_EXCEEDED"):
        check_position_cap("free", existing_notional=4500.0, new_notional=600.0)  # 5100 > 5000


def test_pro_tier_no_position_cap():
    check_position_cap("pro", existing_notional=999999.0, new_notional=999999.0)  # no limit
