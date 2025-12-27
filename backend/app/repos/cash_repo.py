from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cash import CashReceipt


class CashReceiptRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> CashReceipt:
        receipt = CashReceipt(**data)
        self.session.add(receipt)
        await self.session.flush()
        return receipt

    async def find_by_sale(self, sale_id):
        result = await self.session.execute(select(CashReceipt).where(CashReceipt.sale_id == sale_id))
        return result.scalars().all()
