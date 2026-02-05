from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_tenant, get_current_user, get_db_session, require_roles, require_module
from app.models.sales import PaymentProvider, SaleStatus
from app.repos.sales_repo import SaleRepo, SaleItemRepo
from app.repos.stock_repo import StockRepo, StockBatchRepo
from app.repos.catalog_repo import ProductRepo
from app.repos.cash_repo import CashReceiptRepo, CashRegisterRepo
from app.repos.payment_repo import PaymentRepo, RefundRepo
from app.repos.tenant_settings_repo import TenantSettingsRepo
from app.repos.shifts_repo import CashierShiftRepo
from app.schemas.sales import (
    RefundCreate,
    SaleComplete,
    SaleCreate,
    SaleDetail,
    SaleDraftCreate,
    SaleDraftUpdate,
    SaleOut,
)
from app.services.sales_service import SalesService

router = APIRouter(
    prefix="/sales",
    tags=["sales"],
    dependencies=[
        Depends(require_roles({"owner", "cashier"})),
        Depends(get_current_tenant),
        Depends(require_module("sales")),
    ],
)


def get_service(session: AsyncSession):
    return SalesService(
        session,
        SaleRepo(session),
        SaleItemRepo(session),
        StockRepo(session),
        StockBatchRepo(session),
        ProductRepo(session),
        CashReceiptRepo(session),
        PaymentRepo(session),
        RefundRepo(session),
        CashRegisterRepo(session),
        TenantSettingsRepo(session),
        CashierShiftRepo(session),
    )


@router.post("", response_model=SaleDetail)
async def create_sale(
    payload: SaleCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
):
    sale, _ = await get_service(session).create_sale(payload.model_dump(), current_user.id, current_tenant.id)
    return sale


@router.post("/draft", response_model=SaleDetail)
async def create_draft_sale(
    payload: SaleDraftCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
):
    sale = await get_service(session).create_draft_sale(payload.model_dump(), current_user.id, current_tenant.id)
    return sale


@router.put("/{sale_id}", response_model=SaleDetail)
async def update_draft_sale_items(
    sale_id: str,
    payload: SaleDraftUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_tenant=Depends(get_current_tenant),
):
    sale = await get_service(session).update_draft_sale_items(sale_id, payload.model_dump(), current_tenant.id)
    return sale


@router.post("/{sale_id}/complete", response_model=SaleDetail)
async def complete_sale(
    sale_id: str,
    payload: SaleComplete,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
):
    sale = await get_service(session).complete_sale(
        sale_id, payload.model_dump(), current_user.id, current_tenant.id
    )
    return sale


@router.post("/{sale_id}/cancel", response_model=SaleDetail)
async def cancel_sale(
    sale_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    sale = await get_service(session).cancel_sale(sale_id)
    return sale


@router.get("", response_model=list[SaleOut])
async def list_sales(
    request: Request,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    cashier_id: str | None = None,
    payment_method: str | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    status_filter = None
    if status:
        try:
            status_filter = SaleStatus(status)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    payment_filter = None
    if payment_method:
        normalized_method = PaymentProvider.normalize(payment_method)
        if not normalized_method:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment method")
        payment_filter = PaymentProvider(normalized_method)
    sales = await get_service(session).list_sales(
        status_filter,
        date_from,
        date_to,
        cashier_id=cashier_id,
        payment_method=payment_filter,
    )
    return sales


@router.get("/{sale_id}", response_model=SaleDetail)
async def get_sale(sale_id: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    sale = await get_service(session).get_sale(sale_id)
    return sale


@router.post("/{sale_id}/void", response_model=SaleDetail, dependencies=[Depends(require_roles({"owner"}))])
async def void_sale(
    sale_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    sale = await get_service(session).void_sale(sale_id, current_user.id)
    return sale


@router.post("/{sale_id}/refunds", response_model=SaleDetail)
async def refund_sale(
    sale_id: str,
    payload: RefundCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    sale = await get_service(session).create_refund(sale_id, payload.model_dump(), current_user.id)
    return sale
