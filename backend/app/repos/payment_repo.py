from sqlalchemy import select
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sales import Payment, Refund


class PaymentRepo:
    def __init__(self, session: AsyncSession, tenant_id):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, sale_id, data: dict) -> Payment:
        payment = Payment(sale_id=sale_id, tenant_id=self.tenant_id, **data)
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def list_by_sale(self, sale_id):
        result = await self.session.execute(
            select(Payment).where(Payment.sale_id == sale_id, Payment.tenant_id == self.tenant_id)
        )
        return result.scalars().all()


class RefundRepo:
    def __init__(self, session: AsyncSession, tenant_id):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, sale_id, data: dict) -> Refund:
        refund = Refund(sale_id=sale_id, tenant_id=self.tenant_id, **data)
        self.session.add(refund)
        await self.session.flush()
        return refund

    async def list_by_sale(self, sale_id):
        result = await self.session.execute(
            select(Refund).where(Refund.sale_id == sale_id, Refund.tenant_id == self.tenant_id)
        )
        return result.scalars().all()
