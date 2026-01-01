from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_tenant, get_db_session, get_current_user, require_roles
from app.schemas.purchasing import SupplierCreate, SupplierUpdate, SupplierOut, PurchaseInvoiceCreate, PurchaseInvoiceOut, PurchaseItemCreate, PurchaseInvoiceDetail, PurchasePostResult
from app.services.purchasing_service import PurchasingService
from app.repos.catalog_repo import ProductRepo
from app.repos.purchasing_repo import SupplierRepo, PurchaseInvoiceRepo, PurchaseItemRepo
from app.repos.stock_repo import StockRepo, StockBatchRepo
from app.models.purchasing import PurchaseStatus

router = APIRouter(
    prefix="",
    tags=["purchasing"],
    dependencies=[Depends(require_roles({"owner", "admin"})), Depends(get_current_tenant)],
)


def get_service(session: AsyncSession, tenant_id):
    return PurchasingService(
        SupplierRepo(session, tenant_id),
        PurchaseInvoiceRepo(session, tenant_id),
        PurchaseItemRepo(session, tenant_id),
        StockRepo(session, tenant_id),
        StockBatchRepo(session, tenant_id),
        ProductRepo(session, tenant_id),
    )


@router.get("/suppliers", response_model=list[SupplierOut])
async def list_suppliers(request: Request, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session, request.state.tenant_id).list_suppliers()


@router.post("/suppliers", response_model=SupplierOut)
async def create_supplier(payload: SupplierCreate, request: Request, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session, request.state.tenant_id).create_supplier(payload.model_dump())


@router.patch("/suppliers/{supplier_id}", response_model=SupplierOut)
async def update_supplier(
    supplier_id: str, payload: SupplierUpdate, request: Request, session: AsyncSession = Depends(get_db_session)
):
    return await get_service(session, request.state.tenant_id).update_supplier(supplier_id, payload.model_dump())


@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    await get_service(session, request.state.tenant_id).delete_supplier(supplier_id)
    return {"detail": "deleted"}


@router.post("/purchase-invoices", response_model=PurchaseInvoiceOut)
async def create_invoice(payload: PurchaseInvoiceCreate, request: Request, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session, request.state.tenant_id).create_invoice(payload.model_dump())


@router.get("/purchase-invoices", response_model=list[PurchaseInvoiceOut])
async def list_invoices(request: Request, status: str | None = None, session: AsyncSession = Depends(get_db_session)):
    status_filter = None
    if status:
        try:
            status_filter = PurchaseStatus(status)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    return await get_service(session, request.state.tenant_id).list_invoices(status_filter)


@router.get("/purchase-invoices/{invoice_id}", response_model=PurchaseInvoiceDetail)
async def get_invoice(invoice_id: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_service(session, request.state.tenant_id)
    invoice = await service.get_invoice(invoice_id)
    return PurchaseInvoiceDetail(**invoice.__dict__, items=invoice.items)


@router.post("/purchase-invoices/{invoice_id}/items", response_model=PurchaseInvoiceDetail)
async def add_purchase_item(invoice_id: str, payload: PurchaseItemCreate, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_service(session, request.state.tenant_id)
    await service.add_item(invoice_id, payload.model_dump())
    invoice = await service.get_invoice(invoice_id)
    return PurchaseInvoiceDetail(**invoice.__dict__, items=invoice.items)


@router.post("/purchase-invoices/{invoice_id}/post", response_model=PurchasePostResult)
async def post_invoice(invoice_id: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    invoice = await get_service(session, request.state.tenant_id).post_invoice(invoice_id)
    return PurchasePostResult(id=invoice.id, status=invoice.status)


@router.post("/purchase-invoices/{invoice_id}/void", response_model=PurchasePostResult)
async def void_invoice(invoice_id: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    invoice = await get_service(session, request.state.tenant_id).void_invoice(invoice_id)
    return PurchasePostResult(id=invoice.id, status=invoice.status)
