from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Role, User, UserRole


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, tenant_id):
        stmt = select(User).where(User.tenant_id == tenant_id).options(selectinload(User.roles))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_email(self, email: str, tenant_id) -> User | None:
        stmt = (
            select(User)
            .where(User.email == email, User.tenant_id == tenant_id)
            .options(selectinload(User.roles))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id, tenant_id) -> User | None:
        stmt = (
            select(User)
            .where(User.id == user_id, User.tenant_id == tenant_id)
            .options(selectinload(User.roles))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self, email: str, password_hash: str, tenant_id, roles: list[Role] | None = None
    ) -> User:
        user = User(email=email, password_hash=password_hash, tenant_id=tenant_id)
        self.session.add(user)
        await self.session.flush()
        if roles:
            await self.set_roles(user, [role.id for role in roles])
        return user

    async def set_roles(self, user: User, role_ids: list):
        await self.session.execute(
            delete(UserRole).where(UserRole.user_id == user.id, UserRole.tenant_id == user.tenant_id)
        )
        for role_id in role_ids:
            await self.session.execute(
                UserRole.__table__.insert().values(
                    user_id=user.id, role_id=role_id, tenant_id=user.tenant_id
                )
            )
        await self.session.flush()


class RoleRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_name(self, name: str, tenant_id) -> Role | None:
        result = await self.session.execute(
            select(Role).where(Role.name == name, Role.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def list(self, tenant_id):
        result = await self.session.execute(select(Role).where(Role.tenant_id == tenant_id))
        return result.scalars().all()

    async def ensure(self, names: set[str], tenant_id):
        result = await self.session.execute(select(Role.name).where(Role.tenant_id == tenant_id))
        existing = {row[0] for row in result}
        for name in names - existing:
            self.session.add(Role(name=name, tenant_id=tenant_id))
        await self.session.flush()
