# core/ai/deepseek_client.py
"""Thin wrapper around DeepSeek API (OpenAI-compatible)."""
import logging
from openai import AsyncOpenAI
from core.config import get_settings

logger = logging.getLogger(__name__)


class DeepSeekClient:
    def __init__(self):
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
        self._model = settings.deepseek_model

    async def analyze(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
        """Send a prompt to DeepSeek and return the response text."""
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"[deepseek] API call failed: {e}")
            raise

    async def close(self):
        await self._client.close()
