from datetime import datetime, timezone
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_utils import set_search_path
from app.core.deps import get_current_tenant, get_current_user, get_db_session
from app.core.security import create_access_token, hash_password
from app.models.invitation import TenantInvitation
from app.models.user import Role, User, UserRole
from app.schemas.auth import InviteInfoResponse, InviteRegisterPayload
from app.schemas.user import LoginPayload, UserOut, TokenOut
from app.services.auth_service import AuthService
from app.services.bootstrap import ensure_roles
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


@router.get("/invite-info", response_model=InviteInfoResponse)
async def invite_info(
    token: str,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    await set_search_path(session, None)
    invitation = await session.scalar(select(TenantInvitation).where(TenantInvitation.token_hash == token_hash))
    if not invitation or invitation.tenant_id != tenant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    now = datetime.now(timezone.utc)
    if invitation.used_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already used")
    if invitation.expires_at and invitation.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite expired")
    await set_search_path(session, tenant.code)
    return InviteInfoResponse(email=invitation.email, tenant_code=tenant.code)


@router.post("/register-invite", response_model=TokenOut)
async def register_invite(
    payload: InviteRegisterPayload,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    await set_search_path(session, None)
    invitation = await session.scalar(select(TenantInvitation).where(TenantInvitation.token_hash == token_hash))
    if not invitation or invitation.tenant_id != tenant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    now = datetime.now(timezone.utc)
    if invitation.used_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already used")
    if invitation.expires_at and invitation.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite expired")
    await set_search_path(session, tenant.code)
    user = await session.scalar(select(User).where(User.email == invitation.email))
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    await ensure_roles(session)
    owner_role = await session.scalar(select(Role).where(Role.name == "owner"))
    user = User(email=invitation.email, password_hash=hash_password(payload.password), is_active=True)
    session.add(user)
    await session.flush()
    await session.execute(UserRole.__table__.insert().values(user_id=user.id, role_id=owner_role.id))
    await set_search_path(session, None)
    invitation.used_at = now
    await session.flush()
    return TokenOut(access_token=create_access_token(str(user.id), ["owner"], tenant.id))
