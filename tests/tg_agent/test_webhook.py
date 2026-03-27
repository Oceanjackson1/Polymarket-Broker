import pytest
from tg_agent.webhook import verify_webhook_secret

def test_verify_webhook_secret_valid():
    assert verify_webhook_secret("abc123", "abc123") is True

def test_verify_webhook_secret_invalid():
    assert verify_webhook_secret("abc123", "wrong") is False

def test_verify_webhook_secret_empty():
    assert verify_webhook_secret("", "") is True
