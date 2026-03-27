from __future__ import annotations
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an intent parser for a Polymarket prediction-market trading agent.
Given a user message, extract the intent as JSON with these fields:
- capability: one of [market_query, place_order, cancel_order, portfolio, analysis, strategy, data_feed, unknown]
- params: a dict of parameters for the capability
- confidence: float 0-1 how confident you are

Capability details:
- market_query: {action: "search"|"detail"|"orderbook", query: str, market_id?: str}
- place_order: {token_id: str, side: "BUY"|"SELL", price: float, size: float}
- cancel_order: {order_id: str}
- portfolio: {action: "positions"|"balance"|"pnl"}
- analysis: {action: "ask"|"scan"|"market", question?: str, market_id?: str}
- strategy: {action: "scan"|"execute", strategy_name?: str}
- data_feed: {feed: "sports"|"nba"|"btc"|"crypto"|"weather", query?: str}
- unknown: when the message doesn't match any capability

Return ONLY valid JSON, no markdown."""


class IntentParser:
    def __init__(self, ai_client: Any, model: str = "deepseek-chat") -> None:
        self._client = ai_client
        self._model = model

    async def parse(self, message: str) -> dict:
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                temperature=0.1,
            )
            raw = resp.choices[0].message.content.strip()
            # Strip markdown code blocks if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(raw)
        except (json.JSONDecodeError, Exception) as exc:
            logger.warning("intent parse failed: %s", exc)
            return {"capability": "unknown", "params": {}, "confidence": 0.0}
