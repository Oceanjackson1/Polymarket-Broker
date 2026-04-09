"""AnalysisService — reusable AI analysis logic shared by FastAPI router and tg_agent handler."""
from __future__ import annotations

import json
import logging
from typing import Any

from api.analysis.prompts import ASK_SYSTEM, SCAN_SYSTEM
from core.ai.deepseek_client import DeepSeekClient
from core.ai.quota import check_and_increment_quota
from core.config import get_settings

logger = logging.getLogger(__name__)


def _parse_ai_json(text: str) -> Any:
    """Extract JSON from AI response, tolerating ```json fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)


class AnalysisService:
    """Stateless analysis service. Shares one DeepSeekClient instance per process."""

    _ai_client: DeepSeekClient | None = None

    def __init__(self, redis: Any):
        self._redis = redis
        self._settings = get_settings()

    @classmethod
    def _get_ai(cls) -> DeepSeekClient:
        if cls._ai_client is None:
            cls._ai_client = DeepSeekClient()
        return cls._ai_client

    async def _enforce_quota(self, user_id: str) -> None:
        """Free tier: 10/day. Raises RuntimeError on exhaustion."""
        limit = self._settings.analysis_daily_quota_free
        if limit <= 0:
            return
        if not self._redis or not user_id:
            return
        allowed, _ = await check_and_increment_quota(self._redis, str(user_id), limit)
        if not allowed:
            raise RuntimeError("ANALYSIS_QUOTA_EXCEEDED")

    async def ask(self, user_id: str, question: str, context: str | None = None) -> str:
        """Natural-language question about prediction markets."""
        if not question:
            return ""
        await self._enforce_quota(user_id)
        prompt = question
        if context:
            prompt += f"\n\nAdditional context: {context}"
        return await self._get_ai().analyze(ASK_SYSTEM, prompt)

    async def scan(
        self,
        user_id: str,
        category: str | None = None,
        min_bias_bps: int = 500,
        limit: int = 10,
    ) -> list[dict]:
        """Scan active markets for AI-detected mispricings."""
        await self._enforce_quota(user_id)

        from core.polymarket.gamma_client import GammaClient
        gamma = GammaClient()
        try:
            params: dict[str, Any] = {"limit": 50, "active": True}
            if category:
                params["tag"] = category
            markets = await gamma.get_markets(**params)
        finally:
            await gamma.close()

        if not markets:
            return []

        summary_lines: list[str] = []
        for m in markets[:20]:
            raw_prices = m.get("outcomePrices", [])
            if isinstance(raw_prices, str):
                try:
                    raw_prices = json.loads(raw_prices)
                except (json.JSONDecodeError, ValueError):
                    raw_prices = []
            price = float(raw_prices[0]) if raw_prices else None
            summary_lines.append(f"- {m['id']}: \"{m.get('question', '?')}\" (price={price})")

        user_prompt = (
            f"Markets to scan (find mispriced ones, min {min_bias_bps} bps bias):\n"
            + "\n".join(summary_lines)
        )
        raw = await self._get_ai().analyze(SCAN_SYSTEM, user_prompt, max_tokens=2048)

        try:
            opportunities = _parse_ai_json(raw)
            if not isinstance(opportunities, list):
                opportunities = []
        except (json.JSONDecodeError, ValueError):
            opportunities = []

        return opportunities[:limit]
