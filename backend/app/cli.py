import argparse
import asyncio
import sys
from sqlalchemy import select

from app.core.config import settings
from app.core.db import async_session
from app.core.security import hash_password, verify_password
from app.models.user import User, Role


async def create_owner():
    email = settings.first_owner_email
    password = settings.first_owner_password
    if not email or not password:
        raise ValueError("FIRST_OWNER_EMAIL and FIRST_OWNER_PASSWORD are required")
    async with async_session() as session:
        role_result = await session.execute(select(Role).where(Role.name == "owner"))
        owner_role = role_result.scalar_one_or_none()
        if not owner_role:
            owner_role = Role(name="owner")
            session.add(owner_role)
            await session.flush()
        user_result = await session.execute(select(User).where(User.email == email))
        user = user_result.scalar_one_or_none()
        if not user:
            user = User(email=email, password_hash=hash_password(password), is_active=True)
            session.add(user)
            await session.flush()
        if not verify_password(password, user.password_hash):
            user.password_hash = hash_password(password)
        if owner_role not in user.roles:
            user.roles.append(owner_role)
        await session.commit()


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("create-owner")
    args = parser.parse_args()
    if args.command == "create-owner":
        try:
            asyncio.run(create_owner())
        except ValueError as exc:
            sys.stderr.write(f"{exc}\n")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
