from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_tenant, get_db_session, require_roles, require_module
from app.schemas.stock import StockAdjustmentCreate, StockMoveOut, StockQuery
from app.services.stock_service import StockService
from app.repos.stock_repo import StockRepo

router = APIRouter(
    prefix="/stock",
    tags=["stock"],
    dependencies=[
        Depends(require_roles({"owner", "admin"})),
        Depends(get_current_tenant),
        Depends(require_module("stock")),
    ],
)


def get_service(session: AsyncSession):
    return StockService(StockRepo(session))


@router.get("", response_model=list[StockQuery])
async def stock_levels(request: Request, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).list_stock()


@router.get("/moves", response_model=list[StockMoveOut])
async def stock_moves(request: Request, product_id: str | None = None, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).list_moves(product_id)


@router.post("/adjustments", response_model=StockMoveOut)
async def adjustments(payload: StockAdjustmentCreate, request: Request, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).adjust(payload.model_dump())
