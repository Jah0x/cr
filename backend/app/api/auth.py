from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session, get_current_user
from app.schemas.user import UserCreate, UserOut, TokenOut
from app.services.auth_service import AuthService
from app.repos.user_repo import UserRepo

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
async def login(payload: UserCreate, session: AsyncSession = Depends(get_db_session)):
    service = AuthService(UserRepo(session))
    token, _ = await service.login(payload.email, payload.password)
    return TokenOut(access_token=token)


@router.post("/logout")
async def logout():
    return {"detail": "logged out"}


@router.post("/register", response_model=UserOut)
async def register(payload: UserCreate, session: AsyncSession = Depends(get_db_session)):
    service = AuthService(UserRepo(session))
    user = await service.register(payload.email, payload.password)
    return user


@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return current_user
