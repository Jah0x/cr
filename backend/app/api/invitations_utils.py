import logging
from datetime import datetime, timezone

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_utils import set_search_path
from app.core.security import create_access_token, hash_password
from app.core.tokens import hash_invite_token
from app.models.invitation import TenantInvitation
from app.models.user import Role, User, UserRole
from app.schemas.user import TokenOut
from app.services.bootstrap import ensure_roles

logger = logging.getLogger(__name__)


def _invite_error(
    *,
    code: str,
    message: str,
    status_code: int,
    token_hash: str,
    invitation: TenantInvitation | None,
    current_tenant_id: str,
) -> JSONResponse:
    token_hash_short = token_hash[:8]
    token_tenant_id = str(invitation.tenant_id) if invitation else None
    expires_at = invitation.expires_at.isoformat() if invitation and invitation.expires_at else None
    used_at = invitation.used_at.isoformat() if invitation and invitation.used_at else None
    logger.info(
        "Invite rejected: code=%s token_hash=%s token_tenant_id=%s current_tenant_id=%s expires_at=%s used_at=%s",
        code,
        token_hash_short,
        token_tenant_id,
        current_tenant_id,
        expires_at,
        used_at,
    )
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


async def validate_invitation(
    *,
    token: str,
    session: AsyncSession,
    tenant,
) -> TenantInvitation | JSONResponse:
    token_hash = hash_invite_token(token)
    await set_search_path(session, None)
    invitation = await session.scalar(select(TenantInvitation).where(TenantInvitation.token_hash == token_hash))
    if not invitation:
        return _invite_error(
            code="INVITE_NOT_FOUND",
            message="Invite not found",
            status_code=status.HTTP_404_NOT_FOUND,
            token_hash=token_hash,
            invitation=None,
            current_tenant_id=str(tenant.id),
        )
    if invitation.tenant_id != tenant.id:
        return _invite_error(
            code="INVITE_TENANT_MISMATCH",
            message="Invite tenant mismatch",
            status_code=status.HTTP_404_NOT_FOUND,
            token_hash=token_hash,
            invitation=invitation,
            current_tenant_id=str(tenant.id),
        )
    now = datetime.now(timezone.utc)
    if invitation.used_at:
        return _invite_error(
            code="INVITE_ALREADY_USED",
            message="Invite already used",
            status_code=status.HTTP_400_BAD_REQUEST,
            token_hash=token_hash,
            invitation=invitation,
            current_tenant_id=str(tenant.id),
        )
    if invitation.expires_at and invitation.expires_at <= now:
        return _invite_error(
            code="INVITE_EXPIRED",
            message="Invite expired",
            status_code=status.HTTP_400_BAD_REQUEST,
            token_hash=token_hash,
            invitation=invitation,
            current_tenant_id=str(tenant.id),
        )
    await set_search_path(session, tenant.code)
    return invitation


async def accept_invitation(
    *,
    token: str,
    password: str,
    session: AsyncSession,
    tenant,
) -> TokenOut | JSONResponse:
    invitation = await validate_invitation(token=token, session=session, tenant=tenant)
    if isinstance(invitation, JSONResponse):
        return invitation
    user = await session.scalar(select(User).where(User.email == invitation.email))
    if user:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {"code": "USER_ALREADY_EXISTS", "message": "User already exists"},
            },
        )
    await ensure_roles(session)
    role_name = invitation.role_name or "owner"
    owner_role = await session.scalar(select(Role).where(Role.name == role_name))
    if not owner_role:
        owner_role = await session.scalar(select(Role).where(Role.name == "owner"))
    user = User(email=invitation.email, password_hash=hash_password(password), is_active=True)
    session.add(user)
    await session.flush()
    await session.execute(UserRole.__table__.insert().values(user_id=user.id, role_id=owner_role.id))
    await set_search_path(session, None)
    invitation.used_at = datetime.now(timezone.utc)
    await session.flush()
    return TokenOut(access_token=create_access_token(str(user.id), ["owner"], tenant.id))
