# tests/test_core/test_ai_client.py
"""Tests for DeepSeek AI client and quota system."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_quota_check_allows_first_call(test_redis):
    from core.ai.quota import check_and_increment_quota
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    # Clean up
    await test_redis.delete(f"analysis_quota:test_ai_user:{today}")

    allowed, remaining = await check_and_increment_quota(test_redis, "test_ai_user", 10)
    assert allowed is True
    assert remaining == 9


async def test_quota_check_blocks_when_exhausted(test_redis):
    from core.ai.quota import check_and_increment_quota
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    key = f"analysis_quota:test_ai_exhaust:{today}"
    await test_redis.set(key, "10")
    await test_redis.expire(key, 86400)

    allowed, remaining = await check_and_increment_quota(test_redis, "test_ai_exhaust", 10)
    assert allowed is False
    assert remaining == 0


async def test_quota_unlimited_when_limit_zero(test_redis):
    from core.ai.quota import check_and_increment_quota
    allowed, remaining = await check_and_increment_quota(test_redis, "test_ai_unlimited", 0)
    assert allowed is True
    assert remaining == 0


async def test_deepseek_client_calls_openai_api():
    from core.ai.deepseek_client import DeepSeekClient

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"result": "test"}'

    with patch("core.ai.deepseek_client.AsyncOpenAI") as MockOpenAI:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        MockOpenAI.return_value = mock_client

        client = DeepSeekClient()
        result = await client.analyze("system prompt", "user prompt")

    assert result == '{"result": "test"}'
    mock_client.chat.completions.create.assert_called_once()
