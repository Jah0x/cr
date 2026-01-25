import asyncio
import logging
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db_utils import set_search_path
from app.core.tokens import hash_invite_token
from app.core.tenancy import normalize_code, normalize_tenant_slug, slugify_tenant_name
from app.models.invitation import TenantInvitation
from app.models.platform import Module, Template
from app.models.tenant import Tenant, TenantStatus
from app.models.tenant_domain import TenantDomain
from app.repos.user_repo import RoleRepo, UserRepo
from app.services.bootstrap import bootstrap_tenant_owner, ensure_tenant_roles, ensure_tenant_schema
from app.services.migrations import get_tenant_migration_status, run_tenant_migrations
from app.services.template_service import apply_template_codes
from app.services.user_service import UserService

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
        correlation_id = str(uuid4())
        schema = normalize_tenant_slug(code)
        name_slug = self._safe_name_slug(name, schema)
        existing = await self.session.scalar(
            select(Tenant).where(
                or_(
                    Tenant.code == schema,
                    func.lower(Tenant.name) == name.strip().lower(),
                    Tenant.code == name_slug,
                )
            )
        )
        if existing:
            logger.info(
                "Tenant already exists: id=%s schema=%s correlation_id=%s",
                existing.id,
                existing.code,
                correlation_id,
            )
            invite = await self._create_invite(existing.code, existing.id, owner_email, role_name="owner")
            await self._ensure_primary_domain(existing, existing.code, name)
            tenant_url = self._tenant_url(existing.code)
            return {
                "tenant": existing,
                "tenant_url": tenant_url,
                "owner_email": owner_email,
                "invite_url": invite["invite_url"],
            }
        tenant = Tenant(name=name, code=schema, status=TenantStatus.inactive)
        self.session.add(tenant)
        await self.session.flush()
        logger.info("Creating tenant schema '%s' correlation_id=%s", schema, correlation_id)
        await ensure_tenant_schema(self.session, schema)
        await self.session.commit()
        try:
            logger.info("Running tenant migrations for '%s' correlation_id=%s", schema, correlation_id)
            await asyncio.to_thread(run_tenant_migrations, schema)
            logger.info("Tenant migrations completed for '%s' correlation_id=%s", schema, correlation_id)
            settings = get_settings()
            if settings.first_owner_password:
                logger.info("Bootstrapping tenant owner for '%s' correlation_id=%s", schema, correlation_id)
                await bootstrap_tenant_owner(schema, owner_email, settings.first_owner_password)
                logger.info("Tenant owner bootstrap completed for '%s' correlation_id=%s", schema, correlation_id)
            else:
                logger.warning(
                    "FIRST_OWNER_PASSWORD not set; creating tenant roles only for '%s' correlation_id=%s",
                    schema,
                    correlation_id,
                )
                await ensure_tenant_roles(schema)
            await self._seed_template(schema, template_id)
            await self._ensure_primary_domain(tenant, schema, name)
            invite = await self._create_invite(schema, tenant.id, owner_email, role_name="owner")
            tenant.status = TenantStatus.active
            tenant.last_error = None
            await self.session.commit()
        except Exception as exc:
            await self._mark_provisioning_failed(tenant, schema, exc, correlation_id=correlation_id)
            detail = {"message": "Tenant provisioning failed", "reason": str(exc), "correlation_id": correlation_id}
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc
        tenant_url = self._tenant_url(schema)
        return {
            "tenant": tenant,
            "tenant_url": tenant_url,
            "owner_email": owner_email,
            "invite_url": invite["invite_url"],
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

    async def get_tenant_status(self, tenant_id: str) -> dict:
        tenant = await self._get_tenant(tenant_id)
        status_info = get_tenant_migration_status(tenant.code)
        return {"tenant": tenant, **status_info}

    async def migrate_tenant(self, tenant_id: str) -> dict:
        tenant = await self._get_tenant(tenant_id)
        correlation_id = str(uuid4())
        try:
            await asyncio.to_thread(run_tenant_migrations, tenant.code)
            tenant.status = TenantStatus.active
            tenant.last_error = None
            await self.session.commit()
        except Exception as exc:
            await self._mark_provisioning_failed(tenant, tenant.code, exc, correlation_id=correlation_id)
            detail = {"message": "Tenant migration failed", "reason": str(exc), "correlation_id": correlation_id}
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail) from exc
        status_info = get_tenant_migration_status(tenant.code)
        return {"tenant": tenant, **status_info}

    async def update_tenant(self, tenant_id: str, *, name: str, status: TenantStatus) -> Tenant:
        tenant = await self._get_tenant(tenant_id)
        tenant.name = name
        tenant.status = status
        tenant.last_error = None if status == TenantStatus.active else tenant.last_error
        await self.session.flush()
        return tenant

    async def list_domains(self, tenant_id: str):
        await set_search_path(self.session, None)
        result = await self.session.execute(
            select(TenantDomain).where(TenantDomain.tenant_id == tenant_id).order_by(TenantDomain.created_at.asc())
        )
        return result.scalars().all()

    async def create_domain(self, tenant_id: str, domain: str, is_primary: bool):
        tenant = await self._get_tenant(tenant_id)
        await set_search_path(self.session, None)
        domain_row = TenantDomain(tenant_id=tenant.id, domain=domain, is_primary=is_primary)
        if is_primary:
            await self.session.execute(
                TenantDomain.__table__.update()
                .where(TenantDomain.tenant_id == tenant.id)
                .values(is_primary=False)
            )
        self.session.add(domain_row)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            await self.session.rollback()
            self._log_db_error("create_domain", exc, tenant_id=str(tenant.id), schema=tenant.code, fields={"domain": domain})
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Domain already exists") from exc
        return domain_row

    async def delete_domain(self, tenant_id: str, domain_id: str):
        await set_search_path(self.session, None)
        domain = await self.session.scalar(
            select(TenantDomain).where(TenantDomain.id == domain_id, TenantDomain.tenant_id == tenant_id)
        )
        if not domain:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")
        was_primary = domain.is_primary
        await self.session.delete(domain)
        await self.session.flush()
        if was_primary:
            next_domain = await self.session.scalar(
                select(TenantDomain)
                .where(TenantDomain.tenant_id == tenant_id)
                .order_by(TenantDomain.created_at.asc(), TenantDomain.id.asc())
                .limit(1)
            )
            if next_domain:
                await self.session.execute(
                    TenantDomain.__table__.update()
                    .where(TenantDomain.tenant_id == tenant_id)
                    .values(is_primary=False)
                )
                next_domain.is_primary = True

    async def set_primary_domain(self, tenant_id: str, domain_id: str) -> TenantDomain:
        await set_search_path(self.session, None)
        domain = await self.session.scalar(
            select(TenantDomain).where(TenantDomain.id == domain_id, TenantDomain.tenant_id == tenant_id)
        )
        if not domain:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")
        if not domain.is_primary:
            await self.session.execute(
                TenantDomain.__table__.update()
                .where(TenantDomain.tenant_id == tenant_id)
                .values(is_primary=False)
            )
            domain.is_primary = True
        await self.session.flush()
        return domain

    async def create_invite(self, tenant_id: str, email: str, role_name: str) -> dict:
        tenant = await self._get_tenant(tenant_id)
        return await self._create_invite(tenant.code, tenant.id, email, role_name=role_name)

    async def list_invites(self, tenant_id: str):
        tenant = await self._get_tenant(tenant_id)
        await set_search_path(self.session, None)
        return (
            await self.session.scalars(
                select(TenantInvitation)
                .where(TenantInvitation.tenant_id == tenant.id)
                .order_by(TenantInvitation.created_at.desc())
            )
        ).all()

    async def regenerate_invite(self, tenant_id: str, invite_id: str) -> dict:
        tenant = await self._get_tenant(tenant_id)
        await set_search_path(self.session, None)
        invitation = await self.session.scalar(
            select(TenantInvitation).where(
                TenantInvitation.id == invite_id,
                TenantInvitation.tenant_id == tenant.id,
            )
        )
        if not invitation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
        invitation.used_at = datetime.now(timezone.utc)
        await self.session.flush()
        return await self._create_invite(
            tenant.code,
            tenant.id,
            invitation.email,
            role_name=invitation.role_name or "owner",
        )

    async def list_users(self, tenant_id: str):
        tenant = await self._get_tenant(tenant_id)
        await set_search_path(self.session, tenant.code)
        try:
            user_repo = UserRepo(self.session)
            return await user_repo.list()
        finally:
            await set_search_path(self.session, None)

    async def create_user(self, tenant_id: str, email: str, password: str, role_names: list[str]):
        tenant = await self._get_tenant(tenant_id)
        await set_search_path(self.session, tenant.code)
        try:
            service = UserService(UserRepo(self.session), RoleRepo(self.session))
            return await service.create_user(email=email, password=password, role_names=role_names)
        except IntegrityError as exc:
            await self.session.rollback()
            self._log_db_error(
                "create_user",
                exc,
                tenant_id=str(tenant.id),
                schema=tenant.code,
                fields={"email": email},
            )
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists") from exc
        finally:
            await set_search_path(self.session, None)

    async def update_user(self, tenant_id: str, user_id: str, *, is_active: bool):
        tenant = await self._get_tenant(tenant_id)
        await set_search_path(self.session, tenant.code)
        try:
            user_repo = UserRepo(self.session)
            user = await user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            user.is_active = is_active
            await self.session.flush()
            return user
        finally:
            await set_search_path(self.session, None)

    async def delete_user(self, tenant_id: str, user_id: str):
        tenant = await self._get_tenant(tenant_id)
        await set_search_path(self.session, tenant.code)
        try:
            user_repo = UserRepo(self.session)
            user = await user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            await self.session.delete(user)
        finally:
            await set_search_path(self.session, None)

    async def _create_invite(self, schema: str, tenant_id, email: str, *, role_name: str = "owner") -> dict:
        await set_search_path(self.session, None)
        now = datetime.now(timezone.utc)
        existing = await self.session.scalar(
            select(TenantInvitation)
            .where(
                TenantInvitation.tenant_id == tenant_id,
                TenantInvitation.email == email,
                TenantInvitation.role_name == role_name,
                TenantInvitation.used_at.is_(None),
                TenantInvitation.expires_at > now,
            )
            .order_by(TenantInvitation.created_at.desc())
        )
        tenant_url = self._tenant_url(schema)
        if existing:
            raw_token = secrets.token_urlsafe(32)
            token_hash = hash_invite_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            existing.token_hash = token_hash
            existing.expires_at = expires_at
            return {
                "invite_url": f"{tenant_url}/register?token={raw_token}",
                "expires_at": expires_at.isoformat(),
            }
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_invite_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        invitation = TenantInvitation(
            tenant_id=tenant_id,
            email=email,
            role_name=role_name,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(invitation)
        await self.session.flush()
        return {
            "invite_url": f"{tenant_url}/register?token={raw_token}",
            "expires_at": expires_at.isoformat(),
        }

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

    def _safe_name_slug(self, name: str, fallback: str) -> str:
        try:
            return slugify_tenant_name(name)
        except ValueError:
            return fallback

    async def _ensure_primary_domain(self, tenant: Tenant, schema: str, name: str) -> TenantDomain:
        await set_search_path(self.session, None)
        slug = self._safe_name_slug(name, schema)
        domain = f"{slug}.securesoft.dev"
        existing = await self.session.scalar(select(TenantDomain).where(TenantDomain.domain == domain))
        if existing:
            if existing.tenant_id != tenant.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Primary domain already in use")
            if not existing.is_primary:
                await self.session.execute(
                    TenantDomain.__table__.update()
                    .where(TenantDomain.tenant_id == tenant.id)
                    .values(is_primary=False)
                )
                existing.is_primary = True
            return existing
        await self.session.execute(
            TenantDomain.__table__.update()
            .where(TenantDomain.tenant_id == tenant.id)
            .values(is_primary=False)
        )
        domain_row = TenantDomain(tenant_id=tenant.id, domain=domain, is_primary=True)
        self.session.add(domain_row)
        await self.session.flush()
        return domain_row

    async def _get_tenant(self, tenant_id: str) -> Tenant:
        tenant = await self.session.get(Tenant, tenant_id)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        return tenant

    async def _mark_provisioning_failed(self, tenant: Tenant, schema: str, exc: Exception, *, correlation_id: str):
        await set_search_path(self.session, None)
        tenant.status = TenantStatus.provisioning_failed
        tenant.last_error = str(exc)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
        self._log_db_error(
            "provision_tenant",
            exc,
            tenant_id=str(tenant.id) if tenant.id else None,
            schema=schema,
        )
        logger.exception(
            "Tenant provisioning failed for schema=%s correlation_id=%s",
            schema,
            correlation_id,
        )

    def _log_db_error(self, action: str, exc: Exception, *, tenant_id: str | None, schema: str | None, fields=None):
        diag = getattr(getattr(exc, "orig", None), "diag", None)
        constraint = getattr(diag, "constraint_name", None)
        table = getattr(diag, "table_name", None)
        column = getattr(diag, "column_name", None)
        logger.error(
            "DB error action=%s table=%s constraint=%s column=%s tenant_id=%s schema=%s fields=%s",
            action,
            table,
            constraint,
            column,
            tenant_id,
            schema,
            fields,
        )
