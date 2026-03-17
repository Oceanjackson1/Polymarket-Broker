import pytest
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_register_creates_user(test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("svc_test@example.com", "password123")
    assert user.email == "svc_test@example.com"
    assert user.id is not None
    assert user.tier == "free"


async def test_register_duplicate_raises(test_db_session):
    svc = AuthService(test_db_session)
    await svc.register("dup@example.com", "pass")
    with pytest.raises(ValueError, match="EMAIL_ALREADY_EXISTS"):
        await svc.register("dup@example.com", "pass")


async def test_login_returns_tokens(test_db_session):
    svc = AuthService(test_db_session)
    await svc.register("login@example.com", "mypassword123")
    result = await svc.login("login@example.com", "mypassword123")
    assert "access_token" in result
    assert "refresh_token" in result


async def test_login_wrong_password_raises(test_db_session):
    svc = AuthService(test_db_session)
    await svc.register("badpw@example.com", "correct")
    with pytest.raises(PermissionError):
        await svc.login("badpw@example.com", "wrong")
