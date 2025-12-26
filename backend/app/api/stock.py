from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session, get_current_user
from app.schemas.stock import StockAdjustmentCreate, StockMoveOut, StockQuery
from app.services.stock_service import StockService
from app.repos.stock_repo import StockRepo

router = APIRouter(prefix="/stock", tags=["stock"], dependencies=[Depends(get_current_user)])


def get_service(session: AsyncSession):
    return StockService(StockRepo(session))


@router.get("", response_model=list[StockQuery])
async def stock_levels(session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).list_stock()


@router.get("/moves", response_model=list[StockMoveOut])
async def stock_moves(product_id: str | None = None, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).list_moves(product_id)


@router.post("/adjustments", response_model=StockMoveOut)
async def adjustments(payload: StockAdjustmentCreate, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).adjust(payload.model_dump())
