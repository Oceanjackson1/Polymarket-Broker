"""Tests for DomeClient — verifies method signatures and request construction."""

import pytest
from unittest.mock import AsyncMock, patch
from core.dome.key_pool import DomeKeyPool
from core.dome.client import DomeClient, extract_list

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture
def dome():
    pool = DomeKeyPool(["test-key-1", "test-key-2"], ws_key_count=0)
    return DomeClient(key_pool=pool, base_url="https://test.domeapi.io/v1")


async def test_get_markets(dome):
    mock_resp = {"data": [{"market_slug": "will-x-happen"}], "has_more": False}
    with patch.object(dome, "_get", new=AsyncMock(return_value=mock_resp)):
        result = await dome.get_markets(status="open", limit=10)
    assert result["data"][0]["market_slug"] == "will-x-happen"


async def test_get_market_price(dome):
    mock_resp = {"price": 0.65, "at_time": 1710000000}
    with patch.object(dome, "_get", new=AsyncMock(return_value=mock_resp)):
        result = await dome.get_market_price("token123")
    assert result["price"] == 0.65


async def test_get_candlesticks(dome):
    mock_resp = {"data": [{"open": 0.5, "high": 0.6, "low": 0.4, "close": 0.55}]}
    with patch.object(dome, "_get", new=AsyncMock(return_value=mock_resp)):
        result = await dome.get_candlesticks("cond123", start_time=100, end_time=200)
    assert len(result["data"]) == 1


async def test_get_kalshi_markets(dome):
    mock_resp = {"data": [{"market_ticker": "NBA-123"}]}
    with patch.object(dome, "_get", new=AsyncMock(return_value=mock_resp)):
        result = await dome.get_kalshi_markets(search="nba")
    assert result["data"][0]["market_ticker"] == "NBA-123"


async def test_get_matching_markets(dome):
    mock_resp = {"data": [{"polymarket": {}, "kalshi": {}}]}
    with patch.object(dome, "_get", new=AsyncMock(return_value=mock_resp)):
        result = await dome.get_matching_markets(polymarket_slugs=["slug1"])
    assert len(result["data"]) == 1


async def test_get_binance_price(dome):
    mock_resp = {"data": [{"symbol": "btcusdt", "value": 65000.0, "timestamp": 123}]}
    with patch.object(dome, "_get", new=AsyncMock(return_value=mock_resp)):
        result = await dome.get_binance_price("btcusdt", limit=1)
    assert result["data"][0]["value"] == 65000.0


async def test_get_wallet_pnl(dome):
    mock_resp = {"pnl_over_time": [{"pnl": 1234.56}]}
    with patch.object(dome, "_get", new=AsyncMock(return_value=mock_resp)):
        result = await dome.get_wallet_pnl("0xabc", granularity="day")
    assert result["pnl_over_time"][0]["pnl"] == 1234.56


async def test_get_positions(dome):
    mock_resp = {"data": [{"token_id": "tok1"}, {"token_id": "tok2"}]}
    with patch.object(dome, "_get", new=AsyncMock(return_value=mock_resp)):
        result = await dome.get_positions("0xabc")
    assert len(result["data"]) == 2


async def test_place_order(dome):
    mock_resp = {"success": True, "orderId": "ord-123"}
    with patch.object(dome, "_post", new=AsyncMock(return_value=mock_resp)):
        result = await dome.place_order(
            user_id="u1", market_id="m1", side="buy",
            size=10.0, price=0.5, signer="0xabc",
        )
    assert result["success"] is True


async def test_429_retry(dome):
    """Verify that a 429 triggers key cooldown and retry."""
    import httpx

    call_count = 0
    fake_request = httpx.Request("GET", "https://test.domeapi.io/v1/test")

    async def mock_request(method, path, *, params=None, json=None, headers=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(429, text="rate limited", request=fake_request)
        return httpx.Response(200, json={"ok": True}, request=fake_request)

    dome._client.request = mock_request
    # _request should retry after 429.
    result = await dome._request("GET", "/test")
    assert result == {"ok": True}
    assert call_count == 2


# ── extract_list tests ───────────────────────────────────────────

def test_extract_list_markets_key():
    assert extract_list({"markets": [{"slug": "a"}], "pagination": {}}) == [{"slug": "a"}]


def test_extract_list_events_key():
    assert extract_list({"events": [{"id": 1}]}) == [{"id": 1}]


def test_extract_list_data_key():
    assert extract_list({"data": [1, 2, 3]}) == [1, 2, 3]


def test_extract_list_prices_key():
    assert extract_list({"prices": [{"value": 100}]}) == [{"value": 100}]


def test_extract_list_raw_list():
    assert extract_list([1, 2]) == [1, 2]


def test_extract_list_empty_dict():
    assert extract_list({}) == []


def test_extract_list_non_dict():
    assert extract_list("string") == []
