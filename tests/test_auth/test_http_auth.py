import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_http_register_returns_201(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "http_test@example.com", "password": "strongpassword123"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "http_test@example.com"
    assert "hashed_password" not in data


async def test_http_register_duplicate_returns_409(client):
    payload = {"email": "http_dup@example.com", "password": "pass123456"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


async def test_http_login_returns_tokens(client):
    await client.post("/api/v1/auth/register", json={
        "email": "http_login@example.com", "password": "mypassword123"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "http_login@example.com", "password": "mypassword123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_http_create_and_list_keys(client):
    await client.post("/api/v1/auth/register", json={
        "email": "http_keys@example.com", "password": "password123"
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "http_keys@example.com", "password": "password123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post("/api/v1/auth/keys",
        json={"name": "My Bot", "scopes": ["markets:read"]}, headers=headers)
    assert create_resp.status_code == 201
    assert create_resp.json()["key"].startswith("pm_live_sk_")

    list_resp = await client.get("/api/v1/auth/keys", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
