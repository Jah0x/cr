from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session, get_current_user, get_current_tenant, require_feature, require_module
from app.services.reports_service import ReportsService
from app.schemas.reports import SummaryReport, GroupReport, TopProductReport, PnlReport, TaxReportItem
from app.models.sales import PaymentProvider

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


@router.get("/pnl", response_model=PnlReport)
async def pnl(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    return await get_service(session).pnl(date_from, date_to)


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


@router.get("/taxes", response_model=list[TaxReportItem])
async def taxes(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    methods: str | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    methods_list = None
    if methods:
        raw = [value.strip() for value in methods.split(",") if value.strip()]
        if not raw:
            return await get_service(session).taxes(date_from, date_to, None)
        valid = {method.value for method in PaymentProvider}
        invalid = [value for value in raw if value not in valid]
        if invalid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid methods: {', '.join(invalid)}",
            )
        methods_list = raw
    return await get_service(session).taxes(date_from, date_to, methods_list)
