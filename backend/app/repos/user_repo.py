from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Role, User, UserRole


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self):
        stmt = select(User).options(selectinload(User.roles))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_email(self, email: str) -> User | None:
        stmt = (
            select(User)
            .where(User.email == email)
            .options(selectinload(User.roles))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id) -> User | None:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, email: str, password_hash: str, roles: list[Role] | None = None) -> User:
        user = User(email=email, password_hash=password_hash)
        self.session.add(user)
        await self.session.flush()
        if roles:
            await self.set_roles(user, [role.id for role in roles])
        return user

    async def set_roles(self, user: User, role_ids: list):
        await self.session.execute(
            delete(UserRole).where(UserRole.user_id == user.id)
        )
        for role_id in role_ids:
            await self.session.execute(
                UserRole.__table__.insert().values(user_id=user.id, role_id=role_id)
            )
        await self.session.flush()


class RoleRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(
            select(Role).where(Role.name == name)
        )
        return result.scalar_one_or_none()

    async def list(self):
        result = await self.session.execute(select(Role))
        return result.scalars().all()

    async def ensure(self, names: set[str]):
        result = await self.session.execute(select(Role.name))
        existing = {row[0] for row in result}
        for name in names - existing:
            self.session.add(Role(name=name))
        await self.session.flush()
