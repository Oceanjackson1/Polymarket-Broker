# api/analysis/router.py
import json
import time
import logging
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from db.postgres import get_session
from db.redis_client import get_redis
from api.deps import get_current_user_from_api_key, require_scope
from api.analysis.schemas import (
    MarketAnalysisResponse, ScanRequest, ScanResponse,
    NbaAnalysisResponse, AskRequest, AskResponse,
)
from api.analysis.prompts import (
    MARKET_ANALYSIS_SYSTEM, MARKET_ANALYSIS_USER,
    SCAN_SYSTEM, NBA_ANALYSIS_SYSTEM, NBA_ANALYSIS_USER, ASK_SYSTEM,
)
from core.ai.deepseek_client import DeepSeekClient
from core.ai.quota import check_and_increment_quota
from core.config import get_settings
from core.polymarket_fees import resolve_category, calc_taker_fee_bps

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["analysis"])
settings = get_settings()

_ai_client: DeepSeekClient | None = None


def _get_ai_client() -> DeepSeekClient:
    global _ai_client
    if _ai_client is None:
        _ai_client = DeepSeekClient()
    return _ai_client


def _get_quota_limit(tier: str) -> int:
    """Free tier: 10/day. Pro/Enterprise: unlimited (0 = no limit)."""
    if tier in ("pro", "enterprise"):
        return 0
    return settings.analysis_daily_quota_free


async def _enforce_quota(redis, auth: dict):
    tier = auth.get("tier", "free")
    limit = _get_quota_limit(tier)
    if limit == 0:
        return  # unlimited
    allowed, remaining = await check_and_increment_quota(redis, str(auth.get("user_id", "")), limit)
    if not allowed:
        raise HTTPException(429, detail="ANALYSIS_QUOTA_EXCEEDED", headers={"X-Analysis-Remaining": "0"})


def _parse_ai_json(text: str) -> dict | list:
    """Extract JSON from AI response, handling markdown code blocks."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]  # remove ```json
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)


@router.get("/market/{market_id}", response_model=MarketAnalysisResponse)
async def analyze_market(
    market_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
    redis=Depends(get_redis),
):
    """AI probability estimate vs current market price."""
    require_scope(auth, "analysis:read")
    await _enforce_quota(redis, auth)

    # Fetch market from Gamma
    from core.polymarket.gamma_client import GammaClient
    gamma = GammaClient()
    try:
        markets = await gamma.get_markets(limit=1, market_id=market_id)
    finally:
        await gamma.close()

    if not markets:
        raise HTTPException(404, detail="MARKET_NOT_FOUND")
    market = markets[0]

    question = market.get("question", "Unknown")
    prices = market.get("outcomePrices", [])
    price = float(prices[0]) if prices else None
    category = ", ".join(market.get("tags", []))

    user_prompt = MARKET_ANALYSIS_USER.format(
        question=question, price=price, category=category, extra_context=""
    )

    ai = _get_ai_client()
    raw = await ai.analyze(MARKET_ANALYSIS_SYSTEM, user_prompt)

    try:
        result = _parse_ai_json(raw)
        ai_prob = float(result.get("probability", 0.5))
        reasoning = result.get("reasoning", raw)
    except (json.JSONDecodeError, ValueError):
        ai_prob = None
        reasoning = raw

    bias_direction = None
    bias_bps = None
    if ai_prob is not None and price is not None:
        delta = abs(ai_prob - price)
        bias_bps = int(delta * 10000)
        if bias_bps < 300:
            bias_direction = "NEUTRAL"
        elif ai_prob > price:
            bias_direction = "AI_HIGHER"
        else:
            bias_direction = "MARKET_HIGHER"

    # Fee-adjusted bias
    tags = market.get("tags", [])
    detected_category = resolve_category(tags)
    poly_fee_bps = calc_taker_fee_bps(detected_category, price) if price else None
    net_bias = (bias_bps - poly_fee_bps) if bias_bps is not None and poly_fee_bps is not None else None

    return MarketAnalysisResponse(
        market_id=market_id,
        question=question,
        current_price=price,
        ai_probability=ai_prob,
        ai_reasoning=reasoning,
        bias_direction=bias_direction,
        bias_bps=bias_bps,
        category=detected_category,
        polymarket_fee_bps=poly_fee_bps,
        net_bias_bps=net_bias,
        model=settings.deepseek_model,
        analyzed_at=datetime.now(UTC),
    )


@router.post("/scan", response_model=ScanResponse)
async def scan_markets(
    body: ScanRequest,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
    redis=Depends(get_redis),
):
    """Full-market scan: top pricing-bias opportunities."""
    require_scope(auth, "analysis:read")
    await _enforce_quota(redis, auth)

    start = time.monotonic()

    # Fetch active markets
    from core.polymarket.gamma_client import GammaClient
    gamma = GammaClient()
    try:
        params = {"limit": 50, "active": True}
        if body.category:
            params["tag"] = body.category
        markets = await gamma.get_markets(**params)
    finally:
        await gamma.close()

    if not markets:
        return ScanResponse(opportunities=[], scan_duration_ms=0, model=settings.deepseek_model, analyzed_at=datetime.now(UTC))

    # Build summary for AI
    market_summary = []
    for m in markets[:20]:  # limit to 20 for token budget
        prices = m.get("outcomePrices", [])
        price = float(prices[0]) if prices else None
        market_summary.append(f"- {m['id']}: \"{m.get('question', '?')}\" (price={price})")

    user_prompt = f"Markets to scan (find mispriced ones, min {body.min_bias_bps} bps bias):\n" + "\n".join(market_summary)

    ai = _get_ai_client()
    raw = await ai.analyze(SCAN_SYSTEM, user_prompt, max_tokens=2048)

    try:
        opportunities = _parse_ai_json(raw)
        if not isinstance(opportunities, list):
            opportunities = []
    except (json.JSONDecodeError, ValueError):
        opportunities = []

    elapsed = int((time.monotonic() - start) * 1000)

    return ScanResponse(
        opportunities=opportunities[:body.limit],
        scan_duration_ms=elapsed,
        model=settings.deepseek_model,
        analyzed_at=datetime.now(UTC),
    )


@router.get("/nba/{game_id}", response_model=NbaAnalysisResponse)
async def analyze_nba_game(
    game_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
    redis=Depends(get_redis),
):
    """AI directional suggestion using NBA fusion data."""
    require_scope(auth, "analysis:read")
    await _enforce_quota(redis, auth)

    from api.data.nba.models import NbaGame
    game = await db.scalar(select(NbaGame).where(NbaGame.game_id == game_id))
    if not game:
        raise HTTPException(404, detail="GAME_NOT_FOUND")

    # Build derivatives context if available
    derivatives_context = ""
    try:
        from api.data.crypto.models import CryptoDerivatives
        deriv = await db.scalar(
            select(CryptoDerivatives)
            .where(CryptoDerivatives.symbol == "BTC")
            .order_by(desc(CryptoDerivatives.recorded_at))
        )
        if deriv:
            derivatives_context = f"Market sentiment: Fear & Greed = {deriv.fear_greed_index}"
    except Exception:
        pass

    user_prompt = NBA_ANALYSIS_USER.format(
        home_team=game.home_team,
        away_team=game.away_team,
        score_home=game.score_home or 0,
        score_away=game.score_away or 0,
        quarter=game.quarter or 1,
        time_remaining=game.time_remaining or "12:00",
        home_prob=float(game.home_win_prob) if game.home_win_prob else "N/A",
        away_prob=float(game.away_win_prob) if game.away_win_prob else "N/A",
        derivatives_context=derivatives_context,
    )

    ai = _get_ai_client()
    raw = await ai.analyze(NBA_ANALYSIS_SYSTEM, user_prompt)

    try:
        result = _parse_ai_json(raw)
        suggestion = result.get("suggestion", "HOLD")
        confidence = float(result.get("confidence", 0.5))
        reasoning = result.get("reasoning", raw)
    except (json.JSONDecodeError, ValueError):
        suggestion = "HOLD"
        confidence = None
        reasoning = raw

    return NbaAnalysisResponse(
        game_id=game_id,
        home_team=game.home_team,
        away_team=game.away_team,
        ai_suggestion=suggestion,
        ai_reasoning=reasoning,
        confidence=confidence,
        context={
            "score": {"home": game.score_home, "away": game.score_away},
            "quarter": game.quarter,
            "time_remaining": game.time_remaining,
            "polymarket": {
                "home_win_prob": float(game.home_win_prob) if game.home_win_prob else None,
                "away_win_prob": float(game.away_win_prob) if game.away_win_prob else None,
            },
        },
        model=settings.deepseek_model,
        analyzed_at=datetime.now(UTC),
    )


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    body: AskRequest,
    auth: dict = Depends(get_current_user_from_api_key),
    redis=Depends(get_redis),
):
    """Natural language query about prediction markets."""
    require_scope(auth, "analysis:read")
    await _enforce_quota(redis, auth)

    user_prompt = body.question
    if body.context:
        user_prompt += f"\n\nAdditional context: {body.context}"

    ai = _get_ai_client()
    answer = await ai.analyze(ASK_SYSTEM, user_prompt)

    return AskResponse(
        question=body.question,
        answer=answer,
        model=settings.deepseek_model,
        analyzed_at=datetime.now(UTC),
    )
