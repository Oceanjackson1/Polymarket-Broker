# api/data/weather/router.py
from datetime import datetime, UTC, date as date_type
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from db.postgres import get_session
from api.deps import get_current_user_from_api_key, require_scope
from api.data.weather.models import WeatherEvent
from api.data.weather.schemas import (
    WeatherDateResponse, WeatherCityResponse, WeatherFusionResponse, TempBin,
)
from core.polymarket.clob_client import ClobClient

router = APIRouter(prefix="/data/weather", tags=["data-weather"])

clob_client = ClobClient()

STALE_THRESHOLD_SECONDS = 600


def _is_stale(updated_at: datetime) -> bool:
    now = datetime.now(UTC)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)
    return (now - updated_at).total_seconds() > STALE_THRESHOLD_SECONDS


@router.get("/dates", response_model=list[WeatherDateResponse])
async def get_weather_dates(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Active dates with weather markets."""
    require_scope(auth, "data:read")
    result = await db.execute(
        select(
            WeatherEvent.event_date,
            func.count(func.distinct(WeatherEvent.city)).label("city_count"),
            func.count(WeatherEvent.id).label("event_count"),
        )
        .group_by(WeatherEvent.event_date)
        .order_by(WeatherEvent.event_date)
    )
    return [
        WeatherDateResponse(date=r.event_date, city_count=r.city_count, event_count=r.event_count)
        for r in result.all()
    ]


@router.get("/dates/{event_date}/cities", response_model=list[WeatherCityResponse])
async def get_weather_cities(
    event_date: date_type = Path(...),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Cities with markets on that date, sorted by max bias."""
    require_scope(auth, "data:read")
    result = await db.execute(
        select(WeatherEvent)
        .where(WeatherEvent.event_date == event_date)
        .order_by(desc(WeatherEvent.max_bias_bps))
    )
    events = list(result.scalars().all())
    return [
        WeatherCityResponse(
            city=e.city,
            event_date=e.event_date,
            max_bias_range=e.max_bias_range,
            max_bias_direction=e.max_bias_direction,
            max_bias_bps=e.max_bias_bps,
            data_updated_at=e.data_updated_at,
        )
        for e in events
    ]


@router.get("/dates/{event_date}/cities/{city}/fusion", response_model=WeatherFusionResponse)
async def get_weather_fusion(
    event_date: date_type = Path(...),
    city: str = Path(...),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Forecast prob x market price x bias per temperature bin."""
    require_scope(auth, "data:read")
    event = await db.scalar(
        select(WeatherEvent).where(
            WeatherEvent.city == city.lower(),
            WeatherEvent.event_date == event_date,
        )
    )
    if not event:
        raise HTTPException(404, detail="WEATHER_EVENT_NOT_FOUND")

    temp_bins = [TempBin(**b) for b in (event.bins_json or [])]

    return WeatherFusionResponse(
        city=event.city,
        date=event.event_date,
        event_slug=event.event_slug,
        temp_unit=event.temp_unit,
        temp_bins=temp_bins,
        max_bias={
            "range": event.max_bias_range,
            "direction": event.max_bias_direction,
            "magnitude_bps": event.max_bias_bps,
        },
        stale=_is_stale(event.data_updated_at),
        data_updated_at=event.data_updated_at,
    )


@router.get("/dates/{event_date}/cities/{city}/orderbook")
async def get_weather_orderbook(
    event_date: date_type = Path(...),
    city: str = Path(...),
    token_id: str = Query(default=""),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Polymarket orderbook for a weather event."""
    require_scope(auth, "data:read")
    event = await db.scalar(
        select(WeatherEvent).where(
            WeatherEvent.city == city.lower(),
            WeatherEvent.event_date == event_date,
        )
    )
    if not event:
        raise HTTPException(404, detail="WEATHER_EVENT_NOT_FOUND")
    if not token_id:
        return {"bins": event.bins_json or [], "event_slug": event.event_slug}
    try:
        return await clob_client.get_orderbook(token_id=token_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")
