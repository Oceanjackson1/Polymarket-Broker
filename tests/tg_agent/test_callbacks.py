import pytest
from tg_agent.callbacks import parse_callback_data


def test_parse_quick_order():
    data = "quick:abc123:BUY:0.65:50"
    parsed = parse_callback_data(data)
    assert parsed["action"] == "quick"
    assert parsed["condition_id"] == "abc123"
    assert parsed["side"] == "BUY"
    assert parsed["price"] == 0.65
    assert parsed["amount"] == 50.0


def test_parse_analyze():
    data = "analyze:abc123"
    parsed = parse_callback_data(data)
    assert parsed["action"] == "analyze"
    assert parsed["condition_id"] == "abc123"


def test_parse_cancel():
    data = "cancel_action"
    parsed = parse_callback_data(data)
    assert parsed["action"] == "cancel_action"
