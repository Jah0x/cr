import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog_nodes import CatalogNode


class CatalogNodeRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        *,
        parent_id: Optional[uuid.UUID] = None,
        level_code: Optional[str] = None,
        filter_parent: bool = False,
    ) -> list[CatalogNode]:
        stmt = select(CatalogNode).where(CatalogNode.is_active.is_(True))
        if filter_parent:
            if parent_id is None:
                stmt = stmt.where(CatalogNode.parent_id.is_(None))
            else:
                stmt = stmt.where(CatalogNode.parent_id == parent_id)
        if level_code:
            stmt = stmt.where(CatalogNode.level_code == level_code)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get(self, node_id) -> CatalogNode | None:
        result = await self.session.execute(select(CatalogNode).where(CatalogNode.id == node_id))
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> CatalogNode:
        node = CatalogNode(**data)
        self.session.add(node)
        await self.session.flush()
        return node
