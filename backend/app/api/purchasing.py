from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session, get_current_user
from app.schemas.purchasing import SupplierCreate, SupplierUpdate, SupplierOut, PurchaseInvoiceCreate, PurchaseInvoiceOut, PurchaseItemCreate, PurchaseInvoiceDetail, PurchasePostResult
from app.services.purchasing_service import PurchasingService
from app.repos.purchasing_repo import SupplierRepo, PurchaseInvoiceRepo, PurchaseItemRepo
from app.repos.stock_repo import StockRepo, StockBatchRepo

router = APIRouter(prefix="", tags=["purchasing"], dependencies=[Depends(get_current_user)])


def get_service(session: AsyncSession):
    return PurchasingService(SupplierRepo(session), PurchaseInvoiceRepo(session), PurchaseItemRepo(session), StockRepo(session), StockBatchRepo(session))


@router.get("/suppliers", response_model=list[SupplierOut])
async def list_suppliers(session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).list_suppliers()


@router.post("/suppliers", response_model=SupplierOut)
async def create_supplier(payload: SupplierCreate, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).create_supplier(payload.model_dump())


@router.patch("/suppliers/{supplier_id}", response_model=SupplierOut)
async def update_supplier(supplier_id: str, payload: SupplierUpdate, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).update_supplier(supplier_id, payload.model_dump())


@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str, session: AsyncSession = Depends(get_db_session)):
    await get_service(session).delete_supplier(supplier_id)
    return {"detail": "deleted"}


@router.post("/purchase-invoices", response_model=PurchaseInvoiceOut)
async def create_invoice(payload: PurchaseInvoiceCreate, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).create_invoice(payload.model_dump())


@router.get("/purchase-invoices", response_model=list[PurchaseInvoiceOut])
async def list_invoices(status: str | None = None, session: AsyncSession = Depends(get_db_session)):
    status_filter = status if status else None
    return await get_service(session).list_invoices(status_filter)


@router.get("/purchase-invoices/{invoice_id}", response_model=PurchaseInvoiceDetail)
async def get_invoice(invoice_id: str, session: AsyncSession = Depends(get_db_session)):
    service = get_service(session)
    invoice = await service.get_invoice(invoice_id)
    return PurchaseInvoiceDetail(**invoice.__dict__, items=invoice.items)


@router.post("/purchase-invoices/{invoice_id}/items", response_model=PurchaseInvoiceDetail)
async def add_purchase_item(invoice_id: str, payload: PurchaseItemCreate, session: AsyncSession = Depends(get_db_session)):
    service = get_service(session)
    await service.add_item(invoice_id, payload.model_dump())
    invoice = await service.get_invoice(invoice_id)
    return PurchaseInvoiceDetail(**invoice.__dict__, items=invoice.items)


@router.post("/purchase-invoices/{invoice_id}/post", response_model=PurchasePostResult)
async def post_invoice(invoice_id: str, session: AsyncSession = Depends(get_db_session)):
    invoice = await get_service(session).post_invoice(invoice_id)
    return PurchasePostResult(id=invoice.id, status=invoice.status)


@router.post("/purchase-invoices/{invoice_id}/void", response_model=PurchasePostResult)
async def void_invoice(invoice_id: str, session: AsyncSession = Depends(get_db_session)):
    invoice = await get_service(session).void_invoice(invoice_id)
    return PurchasePostResult(id=invoice.id, status=invoice.status)
