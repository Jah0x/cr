from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_tenant, get_db_session, get_current_user, require_roles
from app.models.sales import SaleStatus
from app.repos.sales_repo import SaleRepo, SaleItemRepo
from app.repos.stock_repo import StockRepo
from app.repos.catalog_repo import ProductRepo
from app.repos.cash_repo import CashReceiptRepo, CashRegisterRepo
from app.repos.payment_repo import PaymentRepo, RefundRepo
from app.schemas.sales import RefundCreate, SaleCreate, SaleOut, SaleDetail
from app.services.sales_service import SalesService

router = APIRouter(
    prefix="/sales",
    tags=["sales"],
    dependencies=[Depends(require_roles({"owner", "cashier"})), Depends(get_current_tenant)],
)


def get_service(session: AsyncSession):
    return SalesService(
        session,
        SaleRepo(session),
        SaleItemRepo(session),
        StockRepo(session),
        ProductRepo(session),
        CashReceiptRepo(session),
        PaymentRepo(session),
        RefundRepo(session),
        CashRegisterRepo(session),
    )


@router.post("", response_model=SaleDetail)
async def create_sale(
    payload: SaleCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    sale, _ = await get_service(session).create_sale(payload.model_dump(), current_user.id)
    return SaleDetail(**sale.__dict__, items=sale.items, receipts=sale.receipts, payments=sale.payments, refunds=sale.refunds)


@router.get("", response_model=list[SaleOut])
async def list_sales(
    request: Request,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    status_filter = None
    if status:
        try:
            status_filter = SaleStatus(status)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    sales = await get_service(session).list_sales(status_filter, date_from, date_to)
    return [SaleOut(**sale.__dict__) for sale in sales]


@router.get("/{sale_id}", response_model=SaleDetail)
async def get_sale(sale_id: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    sale = await get_service(session).get_sale(sale_id)
    return SaleDetail(**sale.__dict__, items=sale.items, receipts=sale.receipts, payments=sale.payments, refunds=sale.refunds)


@router.post("/{sale_id}/void", response_model=SaleDetail, dependencies=[Depends(require_roles({"owner"}))])
async def void_sale(
    sale_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    sale = await get_service(session).void_sale(sale_id, current_user.id)
    return SaleDetail(**sale.__dict__, items=sale.items, receipts=sale.receipts, payments=sale.payments, refunds=sale.refunds)


@router.post("/{sale_id}/refunds", response_model=SaleDetail)
async def refund_sale(
    sale_id: str,
    payload: RefundCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    sale = await get_service(session).create_refund(sale_id, payload.model_dump(), current_user.id)
    return SaleDetail(**sale.__dict__, items=sale.items, receipts=sale.receipts, payments=sale.payments, refunds=sale.refunds)
