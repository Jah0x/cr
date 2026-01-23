import asyncio
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db_utils import set_search_path
from app.core.tenancy import normalize_code, normalize_tenant_slug
from app.models.invitation import TenantInvitation
from app.models.platform import Module, Template
from app.models.tenant import Tenant, TenantStatus
from app.services.bootstrap import bootstrap_tenant_owner, ensure_tenant_roles, ensure_tenant_schema
from app.services.migrations import run_tenant_migrations
from app.services.template_service import apply_template_codes

logger = logging.getLogger(__name__)


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
        template_id: str | None = None,
    ):
        schema = normalize_tenant_slug(code)
        existing = await self.session.scalar(select(Tenant).where(Tenant.code == schema))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant code already exists")
        tenant = Tenant(name=name, code=schema, status=TenantStatus.active)
        self.session.add(tenant)
        await self.session.flush()
        logger.info("Creating tenant schema '%s'", schema)
        await ensure_tenant_schema(self.session, schema)
        await self.session.commit()
        try:
            logger.info("Running tenant migrations for '%s'", schema)
            await asyncio.to_thread(run_tenant_migrations, schema)
            logger.info("Tenant migrations completed for '%s'", schema)
        except Exception as exc:
            logger.exception("Tenant migrations failed for '%s'", schema)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Tenant migrations failed: {exc}",
            ) from exc
        settings = get_settings()
        if settings.first_owner_password:
            logger.info("Bootstrapping tenant owner for '%s'", schema)
            await bootstrap_tenant_owner(schema, owner_email, settings.first_owner_password)
            logger.info("Tenant owner bootstrap completed for '%s'", schema)
        else:
            logger.warning("FIRST_OWNER_PASSWORD not set; creating tenant roles only for '%s'", schema)
            await ensure_tenant_roles(schema)
        await self._seed_template(schema, template_id)
        invite_url = await self._create_invite(schema, tenant.id, owner_email)
        tenant_url = self._tenant_url(schema)
        return {
            "tenant": tenant,
            "tenant_url": tenant_url,
            "owner_email": owner_email,
            "invite_url": invite_url,
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
        module = Module(code=normalize_code(code), name=name, description=description, is_active=is_active)
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
            module_codes=[normalize_code(code) for code in module_codes],
            feature_codes=[normalize_code(code) for code in feature_codes],
        )
        self.session.add(template)
        await self.session.flush()
        return template

    async def _create_invite(self, schema: str, tenant_id, owner_email: str) -> str:
        await set_search_path(self.session, None)
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        invitation = TenantInvitation(
            tenant_id=tenant_id,
            email=owner_email,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(invitation)
        await self.session.flush()
        tenant_url = self._tenant_url(schema)
        return f"{tenant_url}/register?token={raw_token}"

    async def _seed_template(self, schema: str, template_id: str | None):
        if not template_id:
            return
        await set_search_path(self.session, None)
        template = await self.session.get(Template, template_id)
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        missing = await apply_template_codes(
            self.session,
            schema=schema,
            module_codes=template.module_codes,
            feature_codes=template.feature_codes,
            validate_modules=True,
        )
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown modules: {', '.join(missing)}",
            )
        await set_search_path(self.session, None)

    def _tenant_url(self, schema: str) -> str:
        settings = get_settings()
        root_domain = settings.root_domain.strip(".")
        if root_domain:
            return f"https://{schema}.{root_domain}"
        if settings.app_host and settings.app_host != "0.0.0.0":
            return f"https://{settings.app_host}"
        return f"https://{schema}.example.com"
