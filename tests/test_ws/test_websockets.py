# tests/test_ws/test_websockets.py
"""
WebSocket tests use Starlette's sync TestClient (required for websocket_connect).
These are intentionally plain `def` tests — no async, no pytest-asyncio — to avoid
event loop conflicts with the session-scoped async fixtures in conftest.py.
"""
import pytest
from unittest.mock import AsyncMock, patch
from starlette.testclient import TestClient


def _get_app():
    from api.main import app
    return app


def test_ws_market_orderbook():
    """Test /ws/markets/{token_id} sends orderbook updates."""
    mock_book = {"bids": [{"price": "0.65", "size": "100"}], "asks": [{"price": "0.70", "size": "50"}]}
    mock_mid = {"mid": "0.675"}

    with patch("api.ws.router._clob") as mock_clob:
        mock_clob.get_orderbook = AsyncMock(return_value=mock_book)
        mock_clob.get_midpoint = AsyncMock(return_value=mock_mid)

        client = TestClient(_get_app())
        with client.websocket_connect("/ws/markets/tok_123") as ws:
            data = ws.receive_json()
            assert data["type"] == "orderbook_update"
            assert data["token_id"] == "tok_123"
            assert data["bids"] == mock_book["bids"]
            assert data["asks"] == mock_book["asks"]
            assert data["midpoint"] == "0.675"


def test_ws_market_orderbook_upstream_error():
    """Test /ws/markets/{token_id} sends error on upstream failure."""
    with patch("api.ws.router._clob") as mock_clob:
        mock_clob.get_orderbook = AsyncMock(side_effect=Exception("CLOB down"))
        mock_clob.get_midpoint = AsyncMock(side_effect=Exception("CLOB down"))

        client = TestClient(_get_app())
        with client.websocket_connect("/ws/markets/tok_err") as ws:
            data = ws.receive_json()
            assert data["type"] == "error"
            assert "Upstream error" in data["message"]


def test_ws_btc_live():
    """Test /ws/btc/live sends BTC data."""
    client = TestClient(_get_app())
    with client.websocket_connect("/ws/btc/live") as ws:
        data = ws.receive_json()
        assert data["type"] == "btc_update"
        assert "data" in data


def test_ws_portfolio_heartbeat():
    """Test /ws/portfolio/live sends heartbeat."""
    client = TestClient(_get_app())
    with client.websocket_connect("/ws/portfolio/live") as ws:
        data = ws.receive_json()
        assert data["type"] == "heartbeat"
        assert data["status"] == "connected"
