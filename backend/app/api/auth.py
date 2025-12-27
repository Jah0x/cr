from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_tenant, get_current_user, get_db_session
from app.schemas.user import LoginPayload, UserOut, TokenOut
from app.services.auth_service import AuthService
from app.repos.user_repo import UserRepo

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
async def login(
    payload: LoginPayload,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    service = AuthService(UserRepo(session))
    token, _ = await service.login(payload.email, payload.password, tenant.id)
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return current_user
