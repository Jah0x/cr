from typing import List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import StockMove, StockBatch


class StockRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_move(self, data: dict) -> StockMove:
        move = StockMove(**data)
        self.session.add(move)
        await self.session.flush()
        return move

    async def list_moves(self, product_id=None) -> List[StockMove]:
        stmt = select(StockMove)
        if product_id:
            stmt = stmt.where(StockMove.product_id == product_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def on_hand(self, product_id) -> float:
        result = await self.session.execute(
            select(func.coalesce(func.sum(StockMove.quantity), 0)).where(StockMove.product_id == product_id)
        )
        return float(result.scalar_one())


class StockBatchRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> StockBatch:
        batch = StockBatch(**data)
        self.session.add(batch)
        await self.session.flush()
        return batch

    async def consume(self, product_id, quantity: float) -> List[StockBatch]:
        batches = await self.session.execute(
            select(StockBatch).where(StockBatch.product_id == product_id, StockBatch.quantity > 0).order_by(StockBatch.id)
        )
        remaining = quantity
        consumed = []
        for batch in batches.scalars():
            if remaining <= 0:
                break
            take = min(float(batch.quantity), remaining)
            batch.quantity = float(batch.quantity) - take
            remaining -= take
            consumed.append((batch, take))
        if remaining > 0:
            raise ValueError("Insufficient stock")
        return consumed
