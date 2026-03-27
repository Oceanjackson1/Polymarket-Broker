import pytest
from tg_agent.tg_formatters import format_markets_response, format_portfolio_response


def test_format_markets_response():
    data = {
        "success": True,
        "markets": [
            {"question": "Will BTC hit 100k?", "best_price": 0.65, "condition_id": "abc"},
            {"question": "Will ETH hit 10k?", "best_price": 0.30, "condition_id": "def"},
        ],
    }
    text = format_markets_response(data)
    assert "BTC" in text
    assert "0.65" in text
    assert "ETH" in text


def test_format_portfolio_response():
    data = {
        "success": True,
        "positions": [
            {"market": "BTC 100k?", "side": "YES", "size": 50, "avg_price": 0.60, "current_price": 0.70},
        ],
    }
    text = format_portfolio_response(data)
    assert "BTC 100k" in text
    assert "YES" in text


def test_format_empty_markets():
    data = {"success": True, "markets": []}
    text = format_markets_response(data)
    assert "0" in text
