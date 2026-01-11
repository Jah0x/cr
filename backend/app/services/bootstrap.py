import asyncio
from sqlalchemy import func, select, text

from app.core.config import settings
from app.core.db_utils import quote_ident, set_search_path, validate_schema_name
from app.core.tenancy import normalize_tenant_slug
from app.core.db import async_session
from app.core.security import hash_password
from app.models.platform import Module, Template
from app.models.tenant import Tenant, TenantStatus
from app.models.user import Role, User, UserRole
from app.models.cash import CashRegister
from app.services.migrations import run_public_migrations, run_tenant_migrations
from app.services.template_service import apply_template_codes


async def ensure_roles(session):
    existing = await session.execute(select(Role.name))
    present = {row[0] for row in existing}
    required = {"owner", "admin", "cashier"}
    for name in required - present:
        session.add(Role(name=name))
    await session.flush()


async def ensure_tenant_schema(session, schema: str):
    validate_schema_name(schema)
    safe_schema = quote_ident(schema)
    await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {safe_schema}"))


async def bootstrap_tenant_owner(schema: str, email: str, password: str):
    async with async_session() as session:
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
    async with async_session() as session:
        schema = normalize_tenant_slug(schema)
        await ensure_tenant_schema(session, schema)
        tenant = await session.scalar(select(Tenant).where(Tenant.code == schema))
        if not tenant:
            tenant = Tenant(name=name, code=schema, status=TenantStatus.active)
            session.add(tenant)
            await session.flush()
        await session.commit()
    await asyncio.to_thread(run_tenant_migrations, schema)
    if owner_email and owner_password:
        await bootstrap_tenant_owner(schema, owner_email, owner_password)


async def seed_platform_defaults():
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
    async with async_session() as session:
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
    async with async_session() as session:
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
        await session.commit()


async def bootstrap_first_tenant():
    await provision_tenant(
        "husky",
        "Husky",
        owner_email=settings.first_owner_email,
        owner_password=settings.first_owner_password,
    )
    await apply_template_by_name("husky", "tobacco")


async def ensure_default_tenant() -> bool:
    async with async_session() as session:
        tenant_count = await session.scalar(select(func.count(Tenant.id)))
    if tenant_count and tenant_count > 0:
        return False
    if not settings.first_owner_email or not settings.first_owner_password:
        raise ValueError("FIRST_OWNER_EMAIL and FIRST_OWNER_PASSWORD are required")
    await bootstrap_first_tenant()
    return True


async def bootstrap_platform():
    await asyncio.to_thread(run_public_migrations)
    await seed_platform_defaults()


async def ensure_cash_register(session):
    existing = await session.execute(select(func.count(CashRegister.id)))
    if existing.scalar_one() > 0:
        return
    register = CashRegister(name="Default", type=settings.cash_register_provider, config={}, is_active=True)
    session.add(register)
    await session.flush()
