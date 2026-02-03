from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sales import Payment, PaymentProvider, Sale, SaleItem
from app.models.stock import SaleItemCostAllocation


class SaleRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> Sale:
        sale = Sale(**data)
        self.session.add(sale)
        await self.session.flush()
        return sale

    async def get(self, sale_id) -> Optional[Sale]:
        stmt = select(Sale).where(Sale.id == sale_id).options(
            selectinload(Sale.items)
            .selectinload(SaleItem.allocations)
            .selectinload(SaleItemCostAllocation.batch),
            selectinload(Sale.receipts),
            selectinload(Sale.payments),
            selectinload(Sale.refunds),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        status_filter=None,
        date_from=None,
        date_to=None,
        cashier_id=None,
        payment_method: PaymentProvider | None = None,
    ) -> List[Sale]:
        stmt = (
            select(Sale)
            .options(
                selectinload(Sale.items)
                .selectinload(SaleItem.allocations)
                .selectinload(SaleItemCostAllocation.batch),
                selectinload(Sale.receipts),
                selectinload(Sale.payments),
            )
        )
        if status_filter:
            stmt = stmt.where(Sale.status == status_filter)
        if date_from:
            stmt = stmt.where(Sale.created_at >= date_from)
        if date_to:
            stmt = stmt.where(Sale.created_at <= date_to)
        if cashier_id:
            stmt = stmt.where(Sale.created_by_user_id == cashier_id)
        if payment_method:
            stmt = stmt.join(Payment).where(Payment.method == payment_method).distinct()
        stmt = stmt.order_by(Sale.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()


class SaleItemRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, sale_id, data: dict) -> SaleItem:
        item = SaleItem(sale_id=sale_id, **data)
        self.session.add(item)
        await self.session.flush()
        return item

    async def get(self, item_id) -> Optional[SaleItem]:
        result = await self.session.execute(
            select(SaleItem).where(SaleItem.id == item_id)
        )
        return result.scalar_one_or_none()
