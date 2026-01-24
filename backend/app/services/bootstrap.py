import asyncio
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy import func, select, text

from app.core.config import get_settings
from app.core.db_utils import quote_ident, set_search_path, validate_schema_name
from app.core.tenancy import normalize_tenant_slug
from app.core.db import get_engine, get_sessionmaker
from app.core.security import hash_password, verify_password
from app.models.platform import Module, Template
from app.models.tenant import Tenant, TenantStatus
from app.models.user import Role, User, UserRole
from app.models.cash import CashRegister
from app.services.migrations import run_public_migrations, run_tenant_migrations, verify_public_migrations
from app.services.template_service import apply_template_codes
from app.repos.tenant_settings_repo import TenantSettingsRepo
from app.services.tenant_settings_service import DEFAULT_TOBACCO_HIERARCHY_SETTINGS

logger = logging.getLogger(__name__)


async def ensure_roles(session):
    existing = await session.execute(select(Role.name))
    present = {row[0] for row in existing}
    required = {"owner", "admin", "cashier"}
    for name in required - present:
        session.add(Role(name=name))
    await session.flush()


async def ensure_tenant_roles(schema: str) -> None:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        await set_search_path(session, schema)
        await ensure_roles(session)
        await session.commit()


async def ensure_tenant_schema(session, schema: str):
    validate_schema_name(schema)
    safe_schema = quote_ident(schema)
    await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {safe_schema}"))


async def bootstrap_tenant_owner(schema: str, email: str, password: str):
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        await set_search_path(session, schema)
        count_result = await session.execute(select(func.count(User.id)))
        if count_result.scalar_one() > 0:
            return
        await ensure_roles(session)
        owner_role = await session.scalar(select(Role).where(Role.name == "owner"))
        user = User(email=email, password_hash=hash_password(password), is_active=True)
        session.add(user)
        await session.flush()
        await session.execute(UserRole.__table__.insert().values(user_id=user.id, role_id=owner_role.id))
        await ensure_cash_register(session)
        # Platform bootstrap runs outside request-scoped transactions; commit explicitly.
        await session.commit()


async def provision_tenant(schema: str, name: str, *, owner_email: str | None = None, owner_password: str | None = None):
    correlation_id = str(uuid.uuid4())
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        schema = normalize_tenant_slug(schema)
        await ensure_tenant_schema(session, schema)
        tenant = await session.scalar(select(Tenant).where(Tenant.code == schema))
        if not tenant:
            tenant = Tenant(name=name, code=schema, status=TenantStatus.inactive)
            session.add(tenant)
            await session.flush()
        await session.commit()
    try:
        logger.info("Running tenant migrations for '%s' correlation_id=%s", schema, correlation_id)
        await asyncio.to_thread(run_tenant_migrations, schema)
        if owner_email and owner_password:
            await bootstrap_tenant_owner(schema, owner_email, owner_password)
        else:
            await ensure_tenant_roles(schema)
        async with sessionmaker() as session:
            tenant = await session.scalar(select(Tenant).where(Tenant.code == schema))
            if tenant:
                tenant.status = TenantStatus.active
                tenant.last_error = None
                await session.commit()
    except Exception as exc:
        logger.exception("Tenant provisioning failed for '%s' correlation_id=%s", schema, correlation_id)
        async with sessionmaker() as session:
            tenant = await session.scalar(select(Tenant).where(Tenant.code == schema))
            if tenant:
                tenant.status = TenantStatus.provisioning_failed
                tenant.last_error = str(exc)
                await session.commit()
        raise


async def seed_platform_defaults():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        res = await session.execute(
            text(
                "select 1 from information_schema.tables "
                "where table_schema='public' limit 1"
            )
        )
        if not res.first():
            raise RuntimeError("Public schema is empty — migrations not applied")
    modules = [
        {
            "code": "catalog",
            "name": "Catalog",
            "description": "Catalog and product management.",
        },
        {
            "code": "purchasing",
            "name": "Purchasing",
            "description": "Suppliers and purchase invoices.",
        },
        {
            "code": "stock",
            "name": "Stock",
            "description": "Stock management and adjustments.",
        },
        {
            "code": "sales",
            "name": "Sales",
            "description": "Sales operations and refunds.",
        },
        {
            "code": "pos",
            "name": "POS",
            "description": "Point of sale operations.",
        },
        {
            "code": "users",
            "name": "Users",
            "description": "User and role management.",
        },
        {
            "code": "reports",
            "name": "Reports",
            "description": "Reporting and analytics.",
        },
        {
            "code": "finance",
            "name": "Finance",
            "description": "Expense tracking and profitability.",
        },
    ]
    templates = [
        {
            "name": "retail",
            "description": "General retail operations.",
            "module_codes": ["catalog", "purchasing", "stock", "sales", "pos", "users", "reports"],
            "feature_codes": ["reports", "ui_prefs"],
        },
        {
            "name": "tobacco",
            "description": "Tobacco shop defaults.",
            "module_codes": ["catalog", "purchasing", "stock", "sales", "pos", "users", "reports", "finance"],
            "feature_codes": ["reports", "ui_prefs", "pos.age_confirm"],
        },
        {
            "name": "ecom",
            "description": "E-commerce focused setup.",
            "module_codes": ["catalog", "stock", "sales", "users", "reports"],
            "feature_codes": ["reports", "ui_prefs"],
        },
        {
            "name": "printshop",
            "description": "Print shop configuration.",
            "module_codes": ["catalog", "stock", "sales", "pos", "users", "reports"],
            "feature_codes": ["reports", "ui_prefs"],
        },
    ]
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        existing_modules = await session.execute(select(Module))
        module_map = {module.code: module for module in existing_modules.scalars()}
        for module in modules:
            if module["code"] in module_map:
                existing = module_map[module["code"]]
                existing.name = module["name"]
                existing.description = module["description"]
                existing.is_active = True
                continue
            session.add(
                Module(
                    code=module["code"],
                    name=module["name"],
                    description=module["description"],
                    is_active=True,
                )
            )
        existing_templates = await session.execute(select(Template))
        template_map = {template.name: template for template in existing_templates.scalars()}
        for template in templates:
            if template["name"] in template_map:
                existing = template_map[template["name"]]
                existing.description = template["description"]
                existing.module_codes = template["module_codes"]
                existing.feature_codes = template["feature_codes"]
                continue
            session.add(
                Template(
                    name=template["name"],
                    description=template["description"],
                    module_codes=template["module_codes"],
                    feature_codes=template["feature_codes"],
                )
            )
        await session.commit()


async def apply_template_by_name(schema: str, template_name: str):
    schema = normalize_tenant_slug(schema)
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        await set_search_path(session, None)
        template = await session.scalar(select(Template).where(Template.name == template_name))
        if not template:
            return
        await set_search_path(session, schema)
        await apply_template_codes(
            session,
            schema=schema,
            module_codes=template.module_codes,
            feature_codes=template.feature_codes,
        )
        tenant = await session.scalar(select(Tenant).where(Tenant.code == schema))
        if tenant and template_name == "tobacco":
            settings_repo = TenantSettingsRepo(session)
            settings_row = await settings_repo.get_or_create(tenant.id)
            current_settings = settings_row.settings or {}
            if "catalog_hierarchy" not in current_settings:
                settings_row.settings = {
                    **current_settings,
                    **DEFAULT_TOBACCO_HIERARCHY_SETTINGS,
                }
                settings_row.updated_at = datetime.now(timezone.utc)
        await session.commit()


async def bootstrap_first_tenant():
    settings = get_settings()
    await provision_tenant(
        "husky",
        "Husky",
        owner_email=settings.first_owner_email,
        owner_password=settings.first_owner_password,
    )
    await apply_template_by_name("husky", "tobacco")


async def ensure_default_tenant() -> bool:
    settings = get_settings()
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        tenant_count = await session.scalar(select(func.count(Tenant.id)))
    if tenant_count and tenant_count > 0:
        return False
    if not settings.first_owner_email or not settings.first_owner_password:
        raise ValueError("FIRST_OWNER_EMAIL and FIRST_OWNER_PASSWORD are required")
    await bootstrap_first_tenant()
    return True


async def bootstrap_platform():
    await asyncio.to_thread(run_public_migrations)
    await verify_public_migrations(get_engine())
    await seed_platform_defaults()


async def ensure_cash_register(session):
    settings = get_settings()
    existing = await session.execute(select(func.count(CashRegister.id)))
    if existing.scalar_one() > 0:
        return
    register = CashRegister(name="Default", type=settings.cash_register_provider, config={}, is_active=True)
    session.add(register)
    await session.flush()


async def ensure_platform_owner() -> bool:
    settings = get_settings()
    if not settings.first_owner_email or not settings.first_owner_password:
        return False
    tenant_slug = settings.default_tenant_slug or "husky"
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        await set_search_path(session, None)
        tenant = await session.scalar(select(Tenant).where(Tenant.code == tenant_slug))
        if not tenant:
            return False
        await set_search_path(session, tenant_slug)
        await ensure_roles(session)
        owner_role = await session.scalar(select(Role).where(Role.name == "owner"))
        user = await session.scalar(select(User).where(User.email == settings.first_owner_email))
        if not user:
            user = User(
                email=settings.first_owner_email,
                password_hash=hash_password(settings.first_owner_password),
                is_active=True,
            )
            session.add(user)
            await session.flush()
        if not verify_password(settings.first_owner_password, user.password_hash):
            user.password_hash = hash_password(settings.first_owner_password)
        role_link = await session.scalar(
            select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == owner_role.id)
        )
        if not role_link:
            await session.execute(UserRole.__table__.insert().values(user_id=user.id, role_id=owner_role.id))
        await session.commit()
    return True
