import pytest
from unittest.mock import AsyncMock, patch
from core.polymarket.gamma_client import GammaClient
from core.polymarket.clob_client import ClobClient
from core.polymarket.eip712 import build_order_struct

pytestmark = pytest.mark.asyncio(loop_scope="session")


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


def test_sign_order_struct_adds_signature():
    # Use a well-known test private key (not used in production)
    test_private_key = "0x0000000000000000000000000000000000000000000000000000000000000001"
    from core.polymarket.eip712 import build_order_struct, sign_order_struct
    order = build_order_struct(
        maker="0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf",
        token_id="21742633",
        price=0.5,
        size=100.0,
        side="BUY",
        fee_rate_bps=10,
        nonce=0,
    )
    signed = sign_order_struct(order, private_key=test_private_key, chain_id=137)
    assert "signature" in signed
    assert signed["signature"].startswith("0x")
    assert len(signed["signature"]) == 132  # 65 bytes = 130 hex chars + "0x"
