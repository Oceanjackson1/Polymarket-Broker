import pytest
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_get_markets_returns_list(client):
    mock_markets = [
        {"id": "0xabc", "question": "Will X win?", "active": True}
    ]
    with patch("api.markets.router.gamma_client") as mock_gamma:
        mock_gamma.get_markets = AsyncMock(return_value=mock_markets)
        resp = await client.get("/api/v1/markets?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert isinstance(data["data"], list)


async def test_get_market_detail(client):
    mock_market = {"id": "0xabc", "question": "Will X win?"}
    with patch("api.markets.router.gamma_client") as mock_gamma:
        mock_gamma.get_market = AsyncMock(return_value=mock_market)
        resp = await client.get("/api/v1/markets/0xabc")
    assert resp.status_code == 200


async def test_get_orderbook(client):
    mock_ob = {"bids": [{"price": "0.65", "size": "100"}], "asks": []}
    with patch("api.markets.router.clob_client") as mock_clob:
        mock_clob.get_orderbook = AsyncMock(return_value=mock_ob)
        resp = await client.get("/api/v1/markets/0xabc/orderbook?token_id=tok123")
    assert resp.status_code == 200
    assert "bids" in resp.json()


async def test_get_midpoint(client):
    mock_mid = {"mid": "0.65", "timestamp": "2026-03-17T10:00:00Z"}
    with patch("api.markets.router.clob_client") as mock_clob:
        mock_clob.get_midpoint = AsyncMock(return_value=mock_mid)
        resp = await client.get("/api/v1/markets/0xabc/midpoint?token_id=tok123")
    assert resp.status_code == 200


async def test_search_markets(client):
    mock_results = [{"id": "0xabc", "question": "Bitcoin price?"}]
    with patch("api.markets.router.gamma_client") as mock_gamma:
        mock_gamma.get_markets = AsyncMock(return_value=mock_results)
        resp = await client.get("/api/v1/markets/search?q=bitcoin")
    assert resp.status_code == 200
    assert "data" in resp.json()
