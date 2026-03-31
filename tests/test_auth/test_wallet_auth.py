import pytest
from eth_account import Account
from eth_account.messages import encode_defunct

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_wallet_challenge_returns_nonce(client):
    account = Account.create()
    resp = await client.post("/api/v1/auth/wallet/challenge",
        json={"wallet_address": account.address})
    assert resp.status_code == 200
    data = resp.json()
    assert "nonce" in data
    assert "expires_at" in data
    assert len(data["nonce"]) == 32  # 16 bytes hex


async def test_wallet_verify_valid_signature(client, test_redis):
    account = Account.create()
    address = account.address

    challenge = await client.post("/api/v1/auth/wallet/challenge",
        json={"wallet_address": address})
    nonce = challenge.json()["nonce"]

    msg = encode_defunct(text=f"Sign in to Polydesk\nNonce: {nonce}")
    signed = account.sign_message(msg)

    verify = await client.post("/api/v1/auth/wallet/verify", json={
        "wallet_address": address,
        "signature": signed.signature.hex(),
    })
    assert verify.status_code == 200
    assert "access_token" in verify.json()
    assert "refresh_token" in verify.json()


async def test_wallet_verify_bad_signature_returns_401(client):
    account = Account.create()
    await client.post("/api/v1/auth/wallet/challenge",
        json={"wallet_address": account.address})
    resp = await client.post("/api/v1/auth/wallet/verify", json={
        "wallet_address": account.address,
        "signature": "0x" + "ab" * 65,
    })
    assert resp.status_code == 401
