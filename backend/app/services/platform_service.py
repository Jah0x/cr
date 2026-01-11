import asyncio
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.platform import Module, Template, TenantFeature, TenantModule
from app.models.tenant import Tenant, TenantStatus
from app.models.user import Role, User, UserRole
from app.services.bootstrap import ensure_tenant_schema, ensure_roles, ensure_cash_register
from app.services.migrations import run_tenant_migrations


class PlatformService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_tenants(self):
        result = await self.session.execute(select(Tenant))
        return result.scalars().all()

    async def create_tenant(
        self,
        *,
        name: str,
        code: str,
        owner_email: str,
        owner_password: str,
        template_id: str | None = None,
    ):
        schema = code.lower()
        existing = await self.session.scalar(select(Tenant).where(Tenant.code == schema))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant code already exists")
        tenant = Tenant(name=name, code=schema, status=TenantStatus.active)
        self.session.add(tenant)
        await self.session.flush()
        await ensure_tenant_schema(self.session, schema)
        await asyncio.to_thread(run_tenant_migrations, schema)
        await self._seed_template(schema, template_id)
        owner_token = await self._bootstrap_owner(schema, owner_email, owner_password, tenant.id)
        tenant_url = self._tenant_url(schema)
        return {
            "tenant": tenant,
            "tenant_url": tenant_url,
            "owner_email": owner_email,
            "owner_password": owner_password,
            "owner_token": owner_token,
        }

    async def apply_template(self, tenant_id: str, template_id: str):
        tenant = await self.session.get(Tenant, tenant_id)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        await self._seed_template(tenant.code, template_id)
        return tenant

    async def list_modules(self):
        result = await self.session.execute(select(Module))
        return result.scalars().all()

    async def create_module(self, *, code: str, name: str, description: str | None, is_active: bool):
        module = Module(code=code, name=name, description=description, is_active=is_active)
        self.session.add(module)
        await self.session.flush()
        return module

    async def list_templates(self):
        result = await self.session.execute(select(Template))
        return result.scalars().all()

    async def create_template(self, *, name: str, description: str | None, module_codes, feature_codes):
        template = Template(
            name=name,
            description=description,
            module_codes=module_codes,
            feature_codes=feature_codes,
        )
        self.session.add(template)
        await self.session.flush()
        return template

    async def _bootstrap_owner(self, schema: str, email: str, password: str, tenant_id):
        await self.session.execute(text("SET LOCAL search_path TO :schema, public"), {"schema": schema})
        user = await self.session.scalar(select(User).where(User.email == email))
        await ensure_roles(self.session)
        owner_role = await self.session.scalar(select(Role).where(Role.name == "owner"))
        if not user:
            user = User(email=email, password_hash=hash_password(password), is_active=True)
            self.session.add(user)
            await self.session.flush()
        existing_role = await self.session.scalar(
            select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == owner_role.id)
        )
        if not existing_role:
            await self.session.execute(UserRole.__table__.insert().values(user_id=user.id, role_id=owner_role.id))
        await ensure_cash_register(self.session)
        await self.session.flush()
        await self.session.execute(text("SET LOCAL search_path TO public"))
        return create_access_token(str(user.id), ["owner"], tenant_id)

    async def _seed_template(self, schema: str, template_id: str | None):
        if not template_id:
            return
        await self.session.execute(text("SET LOCAL search_path TO public"))
        template = await self.session.get(Template, template_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        await self.session.execute(text("SET LOCAL search_path TO :schema, public"), {"schema": schema})
        module_codes = list(dict.fromkeys(template.module_codes or []))
        feature_codes = list(dict.fromkeys(template.feature_codes or []))
        if module_codes:
            modules = await self.session.execute(select(Module).where(Module.code.in_(module_codes)))
            module_map = {module.code: module for module in modules.scalars()}
            missing = [code for code in module_codes if code not in module_map]
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown modules: {', '.join(missing)}",
                )
            existing_modules = await self.session.execute(
                select(TenantModule.module_id)
            )
            existing_ids = {row[0] for row in existing_modules}
            for module in module_map.values():
                if module.id in existing_ids:
                    continue
                self.session.add(
                    TenantModule(
                        module_id=module.id,
                        is_enabled=True,
                        created_at=datetime.now(timezone.utc),
                    )
                )
        if feature_codes:
            existing_features = await self.session.execute(
                select(TenantFeature.code)
            )
            existing_codes = {row[0] for row in existing_features}
            for code in feature_codes:
                if code in existing_codes:
                    continue
                self.session.add(
                    TenantFeature(
                        code=code,
                        is_enabled=True,
                        created_at=datetime.now(timezone.utc),
                    )
                )
        await self.session.execute(text("SET LOCAL search_path TO public"))

    def _tenant_url(self, schema: str) -> str:
        root_domain = settings.root_domain.strip(".")
        if root_domain:
            return f"https://{schema}.{root_domain}"
        if settings.app_host and settings.app_host != "0.0.0.0":
            return f"https://{settings.app_host}"
        return f"https://{schema}.example.com"
