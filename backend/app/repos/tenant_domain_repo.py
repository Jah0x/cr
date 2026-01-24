from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant_domain import TenantDomain


class TenantDomainRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_domain(self, domain: str) -> TenantDomain | None:
        normalized = domain.lower().strip()
        result = await self.session.execute(select(TenantDomain).where(TenantDomain.domain == normalized))
        return result.scalar_one_or_none()

    async def list_by_tenant(self, tenant_id):
        result = await self.session.execute(select(TenantDomain).where(TenantDomain.tenant_id == tenant_id))
        return result.scalars().all()
