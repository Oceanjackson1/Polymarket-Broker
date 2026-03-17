import hmac as _hmac
import hashlib
import secrets
from datetime import datetime, timedelta, UTC

from cryptography.fernet import Fernet
from jose import jwt, JWTError

from core.config import get_settings

settings = get_settings()
_fernet = Fernet(settings.fernet_key.encode())


def encrypt_api_key(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_api_key(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode()).decode()


def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    mins = expires_minutes if expires_minutes is not None else settings.access_token_expire_minutes
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + timedelta(minutes=mins)
    payload["type"] = "access"
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e


def decode_access_token(token: str) -> dict:
    payload = _decode_token(token)
    if payload.get("type") != "access":
        raise ValueError("Invalid token: not an access token")
    return payload


def decode_refresh_token(token: str) -> dict:
    payload = _decode_token(token)
    if payload.get("type") != "refresh":
        raise ValueError("Invalid token: not a refresh token")
    if "jti" not in payload:
        raise ValueError("Invalid token: missing jti")
    return payload


def generate_api_key_value(prefix: str = "pm_live_sk") -> str:
    return f"{prefix}_{secrets.token_urlsafe(24)}"


def hmac_sign(secret: str, body: bytes) -> str:
    sig = _hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def hmac_verify(secret: str, body: bytes, signature: str) -> bool:
    expected = hmac_sign(secret, body)
    return _hmac.compare_digest(expected, signature)
