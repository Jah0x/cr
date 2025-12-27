from typing import List
from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import StockMove, StockBatch


class StockRepo:
    def __init__(self, session: AsyncSession, tenant_id):
        self.session = session
        self.tenant_id = tenant_id

    async def record_move(self, data: dict) -> StockMove:
        payload = data.copy()
        if "delta_qty" not in payload and "quantity" in payload:
            payload["delta_qty"] = payload["quantity"]
        if "quantity" not in payload and "delta_qty" in payload:
            payload["quantity"] = payload["delta_qty"]
        move = StockMove(**payload, tenant_id=self.tenant_id)
        self.session.add(move)
        await self.session.flush()
        return move

    async def list_moves(self, product_id=None) -> List[StockMove]:
        stmt = select(StockMove).where(StockMove.tenant_id == self.tenant_id)
        if product_id:
            stmt = stmt.where(StockMove.product_id == product_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_on_hand(self, product_id=None):
        sum_expr = func.coalesce(func.sum(StockMove.delta_qty), 0)
        fallback_expr = func.coalesce(func.sum(StockMove.quantity), 0)
        stmt = (
            select(StockMove.product_id, func.coalesce(sum_expr, fallback_expr).label("on_hand"))
            .where(StockMove.tenant_id == self.tenant_id)
            .group_by(StockMove.product_id)
        )
        if product_id:
            stmt = stmt.where(StockMove.product_id == product_id)
        result = await self.session.execute(stmt)
        return result.all()

    async def on_hand(self, product_id) -> float:
        sum_expr = func.coalesce(func.sum(StockMove.delta_qty), 0)
        fallback_expr = func.coalesce(func.sum(StockMove.quantity), 0)
        result = await self.session.execute(
            select(func.coalesce(sum_expr, fallback_expr)).where(
                StockMove.product_id == product_id, StockMove.tenant_id == self.tenant_id
            )
        )
        return float(result.scalar_one())


class StockBatchRepo:
    def __init__(self, session: AsyncSession, tenant_id):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, data: dict) -> StockBatch:
        batch = StockBatch(**data, tenant_id=self.tenant_id)
        self.session.add(batch)
        await self.session.flush()
        return batch

    async def consume(self, product_id, quantity: float) -> List[StockBatch]:
        batches = await self.session.execute(
            select(StockBatch)
            .where(StockBatch.product_id == product_id, StockBatch.quantity > 0, StockBatch.tenant_id == self.tenant_id)
            .order_by(StockBatch.id)
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
