from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_session
from api.deps import get_current_user_from_api_key
from api.portfolio.service import PortfolioService
from api.portfolio.schemas import PositionsResponse, BalanceResponse, PnlResponse

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/positions", response_model=PositionsResponse)
async def get_positions(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    positions = await PortfolioService(db).get_positions(user_id=auth["user_id"])
    return PositionsResponse(positions=positions)


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    result = await PortfolioService(db).get_balance(user_id=auth["user_id"])
    return BalanceResponse(**result)


@router.get("/pnl", response_model=PnlResponse)
async def get_pnl(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    result = await PortfolioService(db).get_pnl(user_id=auth["user_id"])
    return PnlResponse(**result)
