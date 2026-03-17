import pytest
from core.security import (
    encrypt_api_key, decrypt_api_key,
    create_access_token, decode_access_token,
    create_refresh_token, decode_refresh_token,
    hmac_sign, hmac_verify,
    generate_api_key_value,
)


def test_fernet_roundtrip():
    plaintext = "pm_live_sk_abc123xyz"
    encrypted = encrypt_api_key(plaintext)
    assert encrypted != plaintext
    assert decrypt_api_key(encrypted) == plaintext


def test_access_token_roundtrip():
    token = create_access_token({"sub": "user_123", "tier": "free"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user_123"
    assert payload["type"] == "access"


def test_access_token_expired_raises():
    token = create_access_token({"sub": "x"}, expires_minutes=-1)
    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token(token)


def test_refresh_token_roundtrip():
    token = create_refresh_token("user_456")
    payload = decode_refresh_token(token)
    assert payload["sub"] == "user_456"
    assert payload["type"] == "refresh"
    assert "jti" in payload


def test_hmac_sign_verify():
    secret = "webhook_secret_key"
    body = b'{"event": "order.filled"}'
    sig = hmac_sign(secret, body)
    assert sig.startswith("sha256=")
    assert hmac_verify(secret, body, sig) is True
    assert hmac_verify(secret, body, "sha256=badsig") is False


def test_generate_api_key_has_correct_prefix():
    key = generate_api_key_value("pm_live_sk")
    assert key.startswith("pm_live_sk_")
    assert len(key) > 20
