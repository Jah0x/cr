from sqlalchemy import func, select

from app.core.config import settings
from app.core.db import async_session
from app.core.security import hash_password
from app.models.tenant import Tenant, TenantStatus
from app.models.user import Role, User, UserRole
from app.models.cash import CashRegister


async def ensure_roles(session):
    existing = await session.execute(select(Role.name))
    present = {row[0] for row in existing}
    required = {"owner", "admin", "cashier"}
    for name in required - present:
        session.add(Role(name=name))
    await session.flush()


async def ensure_default_tenant(session):
    tenant = await session.scalar(select(Tenant).where(Tenant.code == "default"))
    if tenant:
        return tenant
    tenant = Tenant(name="Default", code="default", status=TenantStatus.active)
    session.add(tenant)
    await session.flush()
    return tenant


async def bootstrap_owner():
    email = settings.first_owner_email
    password = settings.first_owner_password
    if not email or not password:
        return
    async with async_session() as session:
        await ensure_default_tenant(session)
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
        await session.commit()


async def ensure_cash_register(session):
    existing = await session.execute(select(func.count(CashRegister.id)))
    if existing.scalar_one() > 0:
        return
    register = CashRegister(name="Default", type=settings.cash_register_provider, config={}, is_active=True)
    session.add(register)
    await session.flush()
