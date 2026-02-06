import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_tenant, get_current_user, get_db_session
from app.api.invitations_utils import accept_invitation, validate_invitation
from app.schemas.auth import InviteInfoResponse, InviteRegisterPayload
from app.schemas.user import LoginPayload, UserOut, TokenOut
from app.services.auth_service import AuthService
from app.repos.user_repo import UserRepo

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenOut)
async def login(
    payload: LoginPayload,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    logger.info(
        "Auth login start: tenant_id=%s tenant_code=%s email=%s",
        tenant.id,
        tenant.code,
        payload.email,
    )
    service = AuthService(UserRepo(session))
    try:
        token, _ = await service.login(payload.email, payload.password, tenant.id)
    except Exception as exc:
        logger.warning(
            "Auth login end: tenant_id=%s tenant_code=%s email=%s status=error error=%s",
            tenant.id,
            tenant.code,
            payload.email,
            exc,
        )
        raise
    logger.info(
        "Auth login end: tenant_id=%s tenant_code=%s email=%s status=success",
        tenant.id,
        tenant.code,
        payload.email,
    )
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
    invitation = await validate_invitation(token=token, session=session, tenant=tenant)
    if isinstance(invitation, JSONResponse):
        return invitation
    return InviteInfoResponse(email=invitation.email, tenant_code=tenant.code)


@router.post("/register-invite", response_model=TokenOut)
async def register_invite(
    payload: InviteRegisterPayload,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    result = await accept_invitation(
        token=payload.token,
        password=payload.password,
        session=session,
        tenant=tenant,
    )
    if isinstance(result, JSONResponse):
        return result
    return result
