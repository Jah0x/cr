from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sales import Sale, SaleItem, Payment


class SaleRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> Sale:
        sale = Sale(**data)
        self.session.add(sale)
        await self.session.flush()
        return sale

    async def get(self, sale_id) -> Optional[Sale]:
        result = await self.session.execute(select(Sale).where(Sale.id == sale_id))
        return result.scalar_one_or_none()

    async def list(self) -> List[Sale]:
        result = await self.session.execute(select(Sale))
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
        result = await self.session.execute(select(SaleItem).where(SaleItem.id == item_id))
        return result.scalar_one_or_none()


class PaymentRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, sale_id, data: dict) -> Payment:
        payment = Payment(sale_id=sale_id, **data)
        self.session.add(payment)
        await self.session.flush()
        return payment
