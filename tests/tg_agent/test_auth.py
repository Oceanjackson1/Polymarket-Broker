import pytest
from tg_agent.auth import TelegramBinding

def test_telegram_binding_model():
    assert hasattr(TelegramBinding, "chat_id")
    assert hasattr(TelegramBinding, "user_id")
    assert hasattr(TelegramBinding, "created_at")
