from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session, get_current_user, get_current_tenant, require_feature, require_module
from app.services.reports_service import ReportsService
from app.schemas.reports import SummaryReport, GroupReport, TopProductReport

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    dependencies=[
        Depends(get_current_user),
        Depends(get_current_tenant),
        Depends(require_module("reports")),
        Depends(require_feature("reports")),
    ],
)


def get_service(session: AsyncSession):
    return ReportsService(session)


@router.get("/summary", response_model=SummaryReport)
async def summary(session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).summary()


@router.get("/by-category", response_model=list[GroupReport])
async def by_category(session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).by_category()


@router.get("/by-brand", response_model=list[GroupReport])
async def by_brand(session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).by_brand()


@router.get("/top-products", response_model=list[TopProductReport])
async def top_products(limit: int = 5, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).top_products(limit)


@router.get("/stock-alerts", response_model=list[TopProductReport])
async def stock_alerts(threshold: float, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).stock_alerts(threshold)
