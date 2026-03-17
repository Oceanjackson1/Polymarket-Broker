import pytest
from unittest.mock import AsyncMock, patch
from core.polymarket.gamma_client import GammaClient
from core.polymarket.clob_client import ClobClient
from core.polymarket.eip712 import build_order_struct


async def test_gamma_get_markets_returns_list():
    client = GammaClient()
    mock_data = [{"id": "0xabc", "question": "Will X happen?"}]
    with patch.object(client, "_get", new=AsyncMock(return_value=mock_data)):
        markets = await client.get_markets(limit=10)
    assert isinstance(markets, list)
    assert markets[0]["id"] == "0xabc"


async def test_clob_get_orderbook_returns_bids_asks():
    client = ClobClient()
    mock_ob = {"bids": [{"price": "0.65", "size": "100"}], "asks": []}
    with patch.object(client, "_get", new=AsyncMock(return_value=mock_ob)):
        ob = await client.get_orderbook(token_id="21742633abc")
    assert "bids" in ob
    assert ob["bids"][0]["price"] == "0.65"


def test_eip712_order_struct_required_fields():
    order = build_order_struct(
        maker="0xabc123",
        token_id="21742633abc",
        price=0.65,
        size=100.0,
        side="BUY",
        fee_rate_bps=10,
        nonce=0,
    )
    for field in ["maker", "tokenId", "makerAmount", "takerAmount", "side", "feeRateBps", "nonce"]:
        assert field in order, f"Missing field: {field}"


def test_eip712_buy_amounts():
    order = build_order_struct(
        maker="0xabc", token_id="tok", price=0.5, size=200.0,
        side="BUY", fee_rate_bps=10, nonce=0,
    )
    # BUY: makerAmount = size * price * 10^6, takerAmount = size * 10^6
    assert order["makerAmount"] == str(int(200.0 * 0.5 * 1_000_000))
    assert order["takerAmount"] == str(int(200.0 * 1_000_000))
