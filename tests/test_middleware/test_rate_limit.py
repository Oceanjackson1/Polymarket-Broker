import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

# In httpx ASGITransport, request.client.host defaults to "127.0.0.1"
_RATE_LIMIT_KEY = "ratelimit:ip:127.0.0.1:calls"


async def test_rate_limit_headers_on_normal_request(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "rl_test@test.com", "password": "pass123"
    })
    assert resp.status_code in (201, 409)
    assert "X-RateLimit-Limit" in resp.headers
    assert "X-RateLimit-Remaining" in resp.headers
    assert "X-RateLimit-Reset" in resp.headers


async def test_rate_limit_remaining_decrements(client, test_redis):
    await test_redis.delete(_RATE_LIMIT_KEY)
    resp1 = await client.post("/api/v1/auth/login", json={"email": "x@x.com", "password": "x"})
    resp2 = await client.post("/api/v1/auth/login", json={"email": "x@x.com", "password": "x"})
    remaining1 = int(resp1.headers.get("X-RateLimit-Remaining", 999))
    remaining2 = int(resp2.headers.get("X-RateLimit-Remaining", 999))
    assert remaining2 <= remaining1


async def test_rate_limit_returns_429_when_exceeded(client, test_redis):
    # Manually exceed the daily limit
    await test_redis.set(_RATE_LIMIT_KEY, 600, ex=60)
    resp = await client.get("/api/v1/auth/keys", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
