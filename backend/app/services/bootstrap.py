from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.db import async_session
from app.core.security import hash_password
from app.models.user import User, Role, UserRole


async def bootstrap_owner():
    email = settings.owner_email
    password = settings.owner_password
    if not email or not password:
        return
    async with async_session() as session:
        role_result = await session.execute(select(Role).where(Role.name == "owner"))
        owner_role = role_result.scalar_one_or_none()
        if not owner_role:
            owner_role = Role(name="owner")
            session.add(owner_role)
            await session.flush()
        existing_owner = await session.execute(select(User).join(User.roles).where(Role.name == "owner"))
        if existing_owner.scalar_one_or_none():
            return
        user_result = await session.execute(select(User).options(selectinload(User.roles)).where(User.email == email))
        user = user_result.scalar_one_or_none()
        if not user:
            user = User(email=email, password_hash=hash_password(password), is_active=True)
            session.add(user)
            await session.flush()
        await session.execute(
            UserRole.__table__.insert().values(user_id=user.id, role_id=owner_role.id)
        )
        await session.commit()
