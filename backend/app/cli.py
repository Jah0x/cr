import argparse
import asyncio
import sys
from sqlalchemy import select

from app.core.config import settings
from app.core.db import async_session, engine
from app.core.db_utils import set_search_path
from app.core.security import hash_password, verify_password
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User, Role, UserRole
from app.services.bootstrap import apply_template_by_name, ensure_roles, ensure_tenant_schema, seed_platform_defaults
from app.services.migrations import run_public_migrations, run_tenant_migrations, verify_public_migrations


async def create_owner(tenant_schema: str):
    email = settings.first_owner_email
    password = settings.first_owner_password
    if not email or not password:
        raise ValueError("FIRST_OWNER_EMAIL and FIRST_OWNER_PASSWORD are required")
    async with async_session() as session:
        await ensure_tenant_schema(session, tenant_schema)
        await set_search_path(session, tenant_schema)
        role_result = await session.execute(select(Role).where(Role.name == "owner"))
        owner_role = role_result.scalar_one_or_none()
        if not owner_role:
            await ensure_roles(session)
            owner_role = await session.scalar(select(Role).where(Role.name == "owner"))
        user_result = await session.execute(
            select(User).where(User.email == email)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            user = User(
                email=email,
                password_hash=hash_password(password),
                is_active=True,
            )
            session.add(user)
            await session.flush()
        if not verify_password(password, user.password_hash):
            user.password_hash = hash_password(password)
        role_link = await session.scalar(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == owner_role.id,
            )
        )
        if not role_link:
            await session.execute(
                UserRole.__table__.insert().values(user_id=user.id, role_id=owner_role.id)
            )
        await session.commit()


async def migrate_all():
    await asyncio.to_thread(run_public_migrations)
    await verify_public_migrations(engine)
    await seed_platform_defaults()
    async with async_session() as session:
        result = await session.execute(select(Tenant))
        tenants = result.scalars().all()
        if not tenants:
            tenant = Tenant(name="Husky", code="husky", status=TenantStatus.active)
            session.add(tenant)
            await session.flush()
            tenants = [tenant]
        for tenant in tenants:
            await ensure_tenant_schema(session, tenant.code)
        await session.commit()
    for tenant in tenants:
        await asyncio.to_thread(run_tenant_migrations, tenant.code)
    husky_present = any(tenant.code == "husky" for tenant in tenants)
    if settings.first_owner_email and settings.first_owner_password and husky_present:
        await create_owner("husky")
    if husky_present:
        await apply_template_by_name("husky", "tobacco")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    create_owner_parser = subparsers.add_parser("create-owner")
    create_owner_parser.add_argument("--tenant", default="husky")
    subparsers.add_parser("migrate-all")
    args = parser.parse_args()
    if args.command == "create-owner":
        try:
            asyncio.run(create_owner(args.tenant))
        except ValueError as exc:
            sys.stderr.write(f"{exc}\n")
            sys.exit(1)
    elif args.command == "migrate-all":
        try:
            asyncio.run(migrate_all())
        except Exception as exc:
            sys.stderr.write(f"{exc}\n")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
