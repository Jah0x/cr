from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import TenantSettings


class TenantSettingsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_tenant_id(self, tenant_id) -> TenantSettings | None:
        result = await self.session.execute(
            select(TenantSettings).where(TenantSettings.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, tenant_id, defaults: dict | None = None) -> TenantSettings:
        existing = await self.get_by_tenant_id(tenant_id)
        if existing:
            return existing
        settings = TenantSettings(tenant_id=tenant_id, settings=defaults or {})
        self.session.add(settings)
        await self.session.flush()
        return settings
