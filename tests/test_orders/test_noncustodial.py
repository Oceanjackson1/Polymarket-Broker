import pytest
import json
import hashlib
from eth_account import Account
from eth_account import messages as eth_msgs

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_build_order_returns_payload_and_hash(client, test_redis):
    # Register + login to get bearer token
    await client.post("/api/v1/auth/register", json={"email": "nc@example.com", "password": "pass123"})
    login = await client.post("/api/v1/auth/login", json={"email": "nc@example.com", "password": "pass123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/orders/build", json={
        "market_id": "0xabc",
        "token_id": "21742633",
        "side": "BUY",
        "price": 0.5,
        "size": 10.0,
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "eip712_payload" in data
    assert "payload_hash" in data
    assert len(data["payload_hash"]) == 64  # SHA-256 hex


async def test_build_order_stored_in_redis(client, test_redis):
    await client.post("/api/v1/auth/register", json={"email": "nc2@example.com", "password": "pass123"})
    login = await client.post("/api/v1/auth/login", json={"email": "nc2@example.com", "password": "pass123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/orders/build", json={
        "market_id": "0xabc", "token_id": "21742633",
        "side": "BUY", "price": 0.5, "size": 10.0,
    }, headers=headers)
    payload_hash = resp.json()["payload_hash"]

    # Verify Redis contains the build params under this hash
    # Key format: order_build:{user_id}:{payload_hash}
    keys = await test_redis.keys(f"order_build:*:{payload_hash}")
    assert len(keys) == 1
