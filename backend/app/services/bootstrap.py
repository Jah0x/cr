import asyncio

from sqlalchemy import func, select, text

from app.core.config import settings
from app.core.db import async_session
from app.core.security import hash_password
from app.models.tenant import Tenant, TenantStatus
from app.models.user import Role, User, UserRole
from app.models.cash import CashRegister
from app.services.migrations import run_public_migrations, run_tenant_migrations


async def ensure_roles(session):
    existing = await session.execute(select(Role.name))
    present = {row[0] for row in existing}
    required = {"owner", "admin", "cashier"}
    for name in required - present:
        session.add(Role(name=name))
    await session.flush()


async def ensure_tenant_schema(session, schema: str):
    safe_schema = f'\"{schema.replace(\"\\\"\", \"\\\"\\\"\")}\"'
    await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {safe_schema}"))


async def bootstrap_tenant_owner(schema: str, email: str, password: str):
    async with async_session() as session:
        await session.execute(text("SET LOCAL search_path TO :schema, public"), {"schema": schema})
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


async def bootstrap_first_tenant():
    await provision_tenant(
        "husky",
        "Husky",
        owner_email=settings.first_owner_email,
        owner_password=settings.first_owner_password,
    )


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


async def ensure_cash_register(session):
    existing = await session.execute(select(func.count(CashRegister.id)))
    if existing.scalar_one() > 0:
        return
    register = CashRegister(name="Default", type=settings.cash_register_provider, config={}, is_active=True)
    session.add(register)
    await session.flush()
