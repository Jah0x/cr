from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.store import Store


class StoreRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_default(self) -> Store:
        result = await self.session.execute(
            select(Store).where(Store.is_default.is_(True)).order_by(Store.created_at.asc())
        )
        store = result.scalar_one_or_none()
        if store:
            return store

        fallback = await self.session.execute(select(Store).order_by(Store.created_at.asc()))
        store = fallback.scalar_one_or_none()
        if store:
            return store

        store = Store(name="Основная точка", is_default=True)
        self.session.add(store)
        await self.session.flush()
        return store
