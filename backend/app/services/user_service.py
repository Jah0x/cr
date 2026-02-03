from fastapi import HTTPException, status

from app.core.security import hash_password
from app.repos.user_repo import RoleRepo, UserRepo


class UserService:
    def __init__(self, user_repo: UserRepo, role_repo: RoleRepo):
        self.user_repo = user_repo
        self.role_repo = role_repo

    async def list_users(self):
        return await self.user_repo.list()

    async def create_user(self, email: str, password: str, role_names: list[str]):
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User exists")
        await self.role_repo.ensure(set(role_names))
        roles = []
        for name in role_names:
            role = await self.role_repo.get_by_name(name)
            if not role:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
            roles.append(role)
        password_hash = hash_password(password)
        user = await self.user_repo.create(email=email, password_hash=password_hash, roles=roles)
        return user

    async def set_roles(self, user_id, role_names: list[str]):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        await self.role_repo.ensure(set(role_names))
        roles = []
        for name in role_names:
            role = await self.role_repo.get_by_name(name)
            if role:
                roles.append(role)
        await self.user_repo.set_roles(user, [role.id for role in roles])
        return await self.user_repo.get_by_id(user_id)

    async def set_password(self, user_id, password: str):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        password_hash = hash_password(password)
        await self.user_repo.set_password_hash(user, password_hash)
        return await self.user_repo.get_by_id(user_id)
