from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.security import hash_password, verify_password, create_access_token
from app.repos.user_repo import UserRepo


class AuthService:
    def __init__(self, user_repo: UserRepo):
        self.user_repo = user_repo

    async def login(self, email: str, password: str):
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
        user.last_login_at = datetime.now(timezone.utc)
        role_names = [role.name for role in user.roles]
        token = create_access_token(str(user.id), role_names)
        return token, user

    async def register(self, email: str, password: str):
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User exists")
        hashed = hash_password(password)
        user = await self.user_repo.create(email=email, password_hash=hashed)
        return user
