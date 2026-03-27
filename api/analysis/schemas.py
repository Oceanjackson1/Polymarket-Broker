# api/analysis/schemas.py
from pydantic import BaseModel
from datetime import datetime


class MarketAnalysisRequest(BaseModel):
    pass  # market_id is a path param


class MarketAnalysisResponse(BaseModel):
    market_id: str
    question: str
    current_price: float | None
    ai_probability: float | None
    ai_reasoning: str
    bias_direction: str | None  # AI_HIGHER, MARKET_HIGHER, NEUTRAL
    bias_bps: int | None
    category: str | None = None
    polymarket_fee_bps: int | None = None
    net_bias_bps: int | None = None
    model: str
    analyzed_at: datetime


class ScanRequest(BaseModel):
    category: str | None = None  # e.g. "sports", "crypto", "politics"
    min_bias_bps: int = 500
    min_net_bias_bps: int | None = None  # filter by post-fee profitability
    limit: int = 10


class ScanResponse(BaseModel):
    opportunities: list[dict]
    scan_duration_ms: int
    model: str
    analyzed_at: datetime


class NbaAnalysisResponse(BaseModel):
    game_id: str
    home_team: str
    away_team: str
    ai_suggestion: str  # "BUY_HOME", "BUY_AWAY", "HOLD"
    ai_reasoning: str
    confidence: float | None
    context: dict  # score, polymarket odds, derivatives if available
    model: str
    analyzed_at: datetime


class AskRequest(BaseModel):
    question: str
    context: str | None = None  # optional additional context


class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    analyzed_at: datetime
