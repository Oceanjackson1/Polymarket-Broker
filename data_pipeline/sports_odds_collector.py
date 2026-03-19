# data_pipeline/sports_odds_collector.py
"""Collects odds from The Odds API and scores, matching against Polymarket events."""
import logging
from datetime import datetime, UTC
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select

from data_pipeline.base import BaseCollector
from api.data.sports.odds_models import SportsOdds, SportsScore
from api.data.sports.models import SportsEvent
from core.sports.odds_api_client import OddsApiClient
from core.config import get_settings

logger = logging.getLogger(__name__)

# Sports to collect (The Odds API sport_keys)
TRACKED_SPORTS = [
    "soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a",
    "soccer_germany_bundesliga", "soccer_france_ligue_one",
    "soccer_uefa_champs_league",
    "basketball_nba", "americanfootball_nfl",
    "baseball_mlb", "icehockey_nhl",
    "mma_mixed_martial_arts", "tennis_atp_french_open",
]

BIAS_THRESHOLD_BPS = 300


def _compute_implied_prob(decimal_odds: float) -> float:
    """Convert decimal odds to implied probability."""
    if decimal_odds <= 1.0:
        return 1.0
    return 1.0 / decimal_odds


def _compute_bias(bookmaker_prob: float | None, polymarket_prob: float | None) -> tuple[str, int]:
    if bookmaker_prob is None or polymarket_prob is None:
        return "NEUTRAL", 0
    delta_bps = int(abs(bookmaker_prob - polymarket_prob) * 10000)
    if delta_bps < BIAS_THRESHOLD_BPS:
        return "NEUTRAL", delta_bps
    if bookmaker_prob > polymarket_prob:
        return "BOOKMAKER_HIGHER", delta_bps
    return "POLYMARKET_HIGHER", delta_bps


def _match_polymarket_event(home: str, away: str, events: list) -> dict | None:
    """Fuzzy match: find Polymarket event whose question contains both team names."""
    home_parts = home.lower().split()
    away_parts = away.lower().split()
    # Use last word of each team name (most distinctive)
    home_key = home_parts[-1] if home_parts else ""
    away_key = away_parts[-1] if away_parts else ""
    for e in events:
        q = (e.question or "").lower()
        if home_key and away_key and home_key in q and away_key in q:
            return e
    return None


class SportsOddsCollector(BaseCollector):
    name = "sports_odds_collector"
    interval_seconds = 300  # 5 minutes

    def __init__(self):
        settings = get_settings()
        self._odds_client = OddsApiClient() if settings.odds_api_key else None

    async def collect(self, db: AsyncSession) -> None:
        if not self._odds_client:
            logger.debug("[sports_odds] no odds_api_key configured, skipping")
            return

        # Pre-fetch Polymarket sports events for matching
        result = await db.execute(
            select(SportsEvent).where(SportsEvent.status == "active")
        )
        pm_events = list(result.scalars().all())

        for sport_key in TRACKED_SPORTS:
            try:
                await self._collect_sport(db, sport_key, pm_events)
            except Exception as e:
                logger.warning(f"[sports_odds] {sport_key} failed: {e}")

        await db.commit()

    async def _collect_sport(self, db: AsyncSession, sport_key: str, pm_events: list) -> None:
        # 1. Get odds
        events = await self._odds_client.get_odds(sport_key)

        for event in events:
            event_id = event.get("id", "")
            home = event.get("home_team", "")
            away = event.get("away_team", "")
            commence = event.get("commence_time")

            # Aggregate odds across bookmakers
            bookmakers = event.get("bookmakers", [])
            home_odds_list = []
            draw_odds_list = []
            away_odds_list = []

            bookmakers_summary = []
            for bm in bookmakers:
                bm_name = bm.get("title", "")
                markets = bm.get("markets", [])
                for market in markets:
                    if market.get("key") != "h2h":
                        continue
                    outcomes = market.get("outcomes", [])
                    bm_entry = {"bookmaker": bm_name}
                    for outcome in outcomes:
                        name = outcome.get("name", "")
                        price = outcome.get("price", 0)
                        if name == home:
                            home_odds_list.append(price)
                            bm_entry["home"] = price
                        elif name == away:
                            away_odds_list.append(price)
                            bm_entry["away"] = price
                        elif name == "Draw":
                            draw_odds_list.append(price)
                            bm_entry["draw"] = price
                    bookmakers_summary.append(bm_entry)

            home_avg = sum(home_odds_list) / len(home_odds_list) if home_odds_list else None
            draw_avg = sum(draw_odds_list) / len(draw_odds_list) if draw_odds_list else None
            away_avg = sum(away_odds_list) / len(away_odds_list) if away_odds_list else None

            home_prob = Decimal(str(round(_compute_implied_prob(home_avg), 4))) if home_avg else None
            away_prob = Decimal(str(round(_compute_implied_prob(away_avg), 4))) if away_avg else None

            # Match against Polymarket
            pm_match = _match_polymarket_event(home, away, pm_events)
            pm_market_id = pm_match.market_id if pm_match else None
            pm_prob = None
            if pm_match and pm_match.outcomes:
                try:
                    pm_prob = Decimal(str(pm_match.outcomes[0].get("price", 0)))
                except (ValueError, TypeError, IndexError):
                    pass

            bias_dir, bias_bps = _compute_bias(
                float(home_prob) if home_prob else None,
                float(pm_prob) if pm_prob else None,
            )

            commence_dt = None
            if commence:
                try:
                    commence_dt = datetime.fromisoformat(commence.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass

            stmt = pg_insert(SportsOdds).values(
                sport_key=sport_key,
                event_id=event_id,
                home_team=home,
                away_team=away,
                commence_time=commence_dt,
                bookmaker_count=len(bookmakers),
                home_odds_avg=Decimal(str(round(home_avg, 4))) if home_avg else None,
                draw_odds_avg=Decimal(str(round(draw_avg, 4))) if draw_avg else None,
                away_odds_avg=Decimal(str(round(away_avg, 4))) if away_avg else None,
                home_implied_prob=home_prob,
                away_implied_prob=away_prob,
                bookmakers_json=bookmakers_summary[:10],
                polymarket_market_id=pm_market_id,
                polymarket_prob=pm_prob,
                bias_direction=bias_dir,
                bias_bps=bias_bps,
                data_updated_at=datetime.now(UTC),
            ).on_conflict_do_update(
                index_elements=["event_id"],
                set_={
                    "home_odds_avg": Decimal(str(round(home_avg, 4))) if home_avg else None,
                    "draw_odds_avg": Decimal(str(round(draw_avg, 4))) if draw_avg else None,
                    "away_odds_avg": Decimal(str(round(away_avg, 4))) if away_avg else None,
                    "home_implied_prob": home_prob,
                    "away_implied_prob": away_prob,
                    "bookmaker_count": len(bookmakers),
                    "bookmakers_json": bookmakers_summary[:10],
                    "polymarket_market_id": pm_market_id,
                    "polymarket_prob": pm_prob,
                    "bias_direction": bias_dir,
                    "bias_bps": bias_bps,
                    "data_updated_at": datetime.now(UTC),
                },
            )
            await db.execute(stmt)

        # 2. Get scores
        try:
            scores = await self._odds_client.get_scores(sport_key)
            for s in scores:
                score_data = s.get("scores") or []
                home_score = away_score = None
                for sc in score_data:
                    if sc.get("name") == s.get("home_team"):
                        home_score = int(sc.get("score", 0) or 0)
                    elif sc.get("name") == s.get("away_team"):
                        away_score = int(sc.get("score", 0) or 0)

                stmt = pg_insert(SportsScore).values(
                    sport_key=sport_key,
                    event_id=s.get("id", ""),
                    home_team=s.get("home_team", ""),
                    away_team=s.get("away_team", ""),
                    home_score=home_score,
                    away_score=away_score,
                    completed=s.get("completed", False),
                    last_update=datetime.now(UTC),
                    scores_json=score_data,
                    data_updated_at=datetime.now(UTC),
                ).on_conflict_do_update(
                    index_elements=["event_id"],
                    set_={
                        "home_score": home_score,
                        "away_score": away_score,
                        "completed": s.get("completed", False),
                        "scores_json": score_data,
                        "data_updated_at": datetime.now(UTC),
                    },
                )
                await db.execute(stmt)
        except Exception as e:
            logger.warning(f"[sports_odds] scores for {sport_key} failed: {e}")
