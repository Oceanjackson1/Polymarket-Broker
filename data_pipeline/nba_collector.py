# data_pipeline/nba_collector.py
from datetime import datetime, UTC
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from data_pipeline.base import BaseCollector
from api.data.nba.models import NbaGame
from core.polymarket.gamma_client import GammaClient

ESPN_SCOREBOARD_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
)
BIAS_THRESHOLD_BPS = 300


def estimate_win_prob(
    score_home: int, score_away: int, quarter: int, time_remaining: str
) -> float:
    """
    Simplified linear win probability model.
    Returns probability that home team wins.
    - At game start (Q1, 12:00 tied): returns 0.5
    - Score differential and time elapsed drive the estimate
    """
    try:
        parts = time_remaining.split(":")
        mins = int(parts[0])
        secs = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, AttributeError, IndexError):
        mins, secs = 6, 0  # default mid-quarter

    # Total minutes elapsed in game
    elapsed = (max(quarter, 1) - 1) * 12.0 + (12.0 - mins - secs / 60.0)
    elapsed = max(0.0, min(elapsed, 48.0))
    time_fraction = elapsed / 48.0

    # Score component: normalize to [-1, 1]
    diff = score_home - score_away
    score_component = max(-1.0, min(1.0, diff / 40.0))

    # As game progresses, score matters more
    prob = 0.5 + score_component * time_fraction * 0.80
    return max(0.05, min(0.95, prob))


def compute_bias(
    statistical_prob: float | None, polymarket_prob: float | None
) -> tuple[str, int]:
    """Returns (direction, magnitude_bps). Direction is from home team's perspective."""
    if statistical_prob is None or polymarket_prob is None:
        return "NEUTRAL", 0
    delta_bps = round(abs(statistical_prob - polymarket_prob) * 10000)
    if delta_bps < BIAS_THRESHOLD_BPS:
        return "NEUTRAL", delta_bps
    if statistical_prob > polymarket_prob:
        return "HOME_UNDERPRICED", delta_bps
    return "AWAY_UNDERPRICED", delta_bps


def _find_market_for_game(home: str, away: str, markets: list) -> dict | None:
    """Fuzzy match: find a Polymarket market whose question contains both team last names."""
    home_last = home.split()[-1].lower()
    away_last = away.split()[-1].lower()
    for m in markets:
        q = m.get("question", "").lower()
        if home_last in q and away_last in q:
            return m
    return None


def _parse_prob_from_market(market: dict, side: str) -> float | None:
    """Extract implied probability from outcomePrices list. side: 'home'=index 0, 'away'=index 1."""
    prices = market.get("outcomePrices", [])
    idx = 0 if side == "home" else 1
    try:
        return float(prices[idx])
    except (IndexError, ValueError, TypeError):
        return None


class NbaCollector(BaseCollector):
    name = "nba_collector"
    interval_seconds = 30

    def __init__(self):
        self._gamma = GammaClient()

    async def collect(self, db: AsyncSession) -> None:
        # 1. Fetch ESPN scoreboard
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(ESPN_SCOREBOARD_URL)
            resp.raise_for_status()
            espn_data = resp.json()

        events = espn_data.get("events", [])
        if not events:
            return

        # 2. Fetch Polymarket NBA markets
        nba_markets = await self._gamma.get_markets(limit=50, tag="nba", active=True)

        # 3. Process each game
        for event in events:
            game_id = event["id"]
            competitions = event.get("competitions", [])
            if not competitions:
                continue
            comp = competitions[0]

            # Parse teams and scores
            home_team = away_team = ""
            score_home = score_away = 0
            for competitor in comp.get("competitors", []):
                name = competitor.get("team", {}).get("displayName", "")
                score = int(competitor.get("score", 0) or 0)
                if competitor.get("homeAway") == "home":
                    home_team, score_home = name, score
                else:
                    away_team, score_away = name, score

            # Parse game status
            status_obj = comp.get("status", {})
            state = status_obj.get("type", {}).get("state", "pre")
            game_status = {"pre": "scheduled", "in": "live", "post": "final"}.get(state, "scheduled")
            quarter = status_obj.get("period", None)
            time_remaining = status_obj.get("displayClock", "")

            # Find matching Polymarket market
            matched_market = _find_market_for_game(home_team, away_team, nba_markets)
            market_id = matched_market["id"] if matched_market else None

            home_prob = away_prob = last_trade = None
            if matched_market:
                home_prob = _parse_prob_from_market(matched_market, "home")
                away_prob = _parse_prob_from_market(matched_market, "away")
                last_trade = home_prob  # approximation

            # Compute bias (only for live games)
            stat_prob = None
            if game_status == "live" and quarter and time_remaining:
                stat_prob = estimate_win_prob(score_home, score_away, quarter, time_remaining)
            bias_direction, bias_bps = compute_bias(stat_prob, home_prob)

            # Upsert to nba_games
            stmt = pg_insert(NbaGame).values(
                game_id=game_id,
                home_team=home_team,
                away_team=away_team,
                game_date=datetime.now(UTC).date(),
                game_status=game_status,
                score_home=score_home,
                score_away=score_away,
                quarter=quarter,
                time_remaining=time_remaining,
                market_id=market_id,
                home_win_prob=home_prob,
                away_win_prob=away_prob,
                last_trade_price=last_trade,
                bias_direction=bias_direction,
                bias_magnitude_bps=bias_bps,
                data_updated_at=datetime.now(UTC),
            ).on_conflict_do_update(
                index_elements=["game_id"],
                set_={
                    "home_team": home_team,
                    "away_team": away_team,
                    "game_status": game_status,
                    "score_home": score_home,
                    "score_away": score_away,
                    "quarter": quarter,
                    "time_remaining": time_remaining,
                    "market_id": market_id,
                    "home_win_prob": home_prob,
                    "away_win_prob": away_prob,
                    "last_trade_price": last_trade,
                    "bias_direction": bias_direction,
                    "bias_magnitude_bps": bias_bps,
                    "data_updated_at": datetime.now(UTC),
                }
            )
            await db.execute(stmt)
        await db.commit()
