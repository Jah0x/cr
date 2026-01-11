from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cash import CashReceipt, CashRegister


class CashReceiptRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> CashReceipt:
        receipt = CashReceipt(**data)
        self.session.add(receipt)
        await self.session.flush()
        return receipt

    async def find_by_sale(self, sale_id):
        result = await self.session.execute(
            select(CashReceipt).where(CashReceipt.sale_id == sale_id)
        )
        return result.scalars().all()


class CashRegisterRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active(self):
        result = await self.session.execute(
            select(CashRegister).where(CashRegister.is_active.is_(True))
        )
        return result.scalars().all()

    async def get_by_id(self, register_id):
        result = await self.session.execute(
            select(CashRegister).where(CashRegister.id == register_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> CashRegister:
        register = CashRegister(**data)
        self.session.add(register)
        await self.session.flush()
        return register
