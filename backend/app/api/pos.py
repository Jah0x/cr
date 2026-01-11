from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_tenant, get_current_user, get_db_session
from app.schemas.sales import SaleCreate, SaleOut, SaleItemCreate, SaleItemUpdate, SaleDetail, PaymentCreate, PaymentOut
from app.services.sales_service import SalesService
from app.repos.sales_repo import SaleRepo, SaleItemRepo
from app.repos.stock_repo import StockRepo, StockBatchRepo
from app.services.payment_providers import PaymentGateway

router = APIRouter(prefix="/pos", tags=["pos"], dependencies=[Depends(get_current_user), Depends(get_current_tenant)])


def get_service(session: AsyncSession):
    return SalesService(
        session,
        SaleRepo(session),
        SaleItemRepo(session),
        StockRepo(session),
        StockBatchRepo(session),
        PaymentGateway(),
    )


@router.post("/sales", response_model=SaleOut)
async def create_sale(payload: SaleCreate, request: Request, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).create_sale(payload.model_dump())


@router.get("/sales/{sale_id}", response_model=SaleDetail)
async def get_sale(sale_id: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    sale = await get_service(session).get_sale(sale_id)
    return SaleDetail(**sale.__dict__, items=sale.items, payments=sale.payments)


@router.post("/sales/{sale_id}/items", response_model=SaleDetail)
async def add_sale_item(sale_id: str, payload: SaleItemCreate, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_service(session)
    await service.add_item(sale_id, payload.model_dump())
    sale = await service.get_sale(sale_id)
    return SaleDetail(**sale.__dict__, items=sale.items, payments=sale.payments)


@router.patch("/sales/{sale_id}/items/{item_id}", response_model=SaleDetail)
async def update_sale_item(
    sale_id: str, item_id: str, payload: SaleItemUpdate, request: Request, session: AsyncSession = Depends(get_db_session)
):
    service = get_service(session)
    await service.update_item(item_id, payload.model_dump())
    sale = await service.get_sale(sale_id)
    return SaleDetail(**sale.__dict__, items=sale.items, payments=sale.payments)


@router.post("/sales/{sale_id}/payments", response_model=PaymentOut)
async def add_payment(sale_id: str, payload: PaymentCreate, request: Request, session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).add_payment(sale_id, payload.model_dump())


@router.post("/sales/{sale_id}/finalize", response_model=SaleOut)
async def finalize_sale(sale_id: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    sale = await get_service(session).finalize(sale_id)
    return SaleOut(id=sale.id, status=sale.status, customer_name=sale.customer_name)


@router.post("/sales/{sale_id}/void", response_model=SaleOut)
async def void_sale(sale_id: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    sale = await get_service(session).void_sale(sale_id)
    return SaleOut(id=sale.id, status=sale.status, customer_name=sale.customer_name)
