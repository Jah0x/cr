from fastapi import HTTPException, status

from app.core.security import hash_password
from app.repos.user_repo import RoleRepo, UserRepo


class UserService:
    allowed_roles = {"cashier", "manager", "owner"}

    def __init__(self, user_repo: UserRepo, role_repo: RoleRepo):
        self.user_repo = user_repo
        self.role_repo = role_repo

    async def list_users(self):
        return await self.user_repo.list()

    def _validate_password(self, password: str):
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password too short",
            )

    def _validate_roles(self, role_names: list[str], allow_owner: bool = True):
        invalid_roles = [name for name in role_names if name not in self.allowed_roles]
        if invalid_roles:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
        if not allow_owner and "owner" in role_names:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner role is not allowed")

    async def create_user(
        self,
        email: str,
        password: str,
        role_names: list[str],
        is_active: bool = True,
    ):
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User exists")
        self._validate_password(password)
        self._validate_roles(role_names, allow_owner=False)
        await self.role_repo.ensure(set(role_names))
        roles = []
        for name in role_names:
            role = await self.role_repo.get_by_name(name)
            if not role:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
            roles.append(role)
        password_hash = hash_password(password)
        user = await self.user_repo.create(
            email=email,
            password_hash=password_hash,
            roles=roles,
            is_active=is_active,
        )
        return user

    async def set_roles(self, user_id, role_names: list[str]):
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        self._validate_roles(role_names)
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
