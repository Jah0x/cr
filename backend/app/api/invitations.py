from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.invitations_utils import accept_invitation, validate_invitation
from app.core.deps import get_current_tenant, get_current_user, get_db_session
from app.schemas.invitations import (
    InvitationAcceptRequest,
    InvitationCreateRequest,
    InvitationCreateResponse,
    InvitationDetailResponse,
)
from app.schemas.user import TokenOut
from app.services.platform_service import PlatformService

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post("", response_model=InvitationCreateResponse)
async def create_invitation(
    payload: InvitationCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
    _current_user=Depends(get_current_user),
):
    service = PlatformService(session)
    invite = await service.create_tenant_invite(tenant, payload.email, payload.role_name)
    return InvitationCreateResponse(invite_url=invite["invite_url"], expires_at=invite["expires_at"])


@router.get("/{token}", response_model=InvitationDetailResponse)
async def get_invitation(
    token: str,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    invitation = await validate_invitation(token=token, session=session, tenant=tenant)
    if isinstance(invitation, JSONResponse):
        return invitation
    return InvitationDetailResponse(email=invitation.email, tenant_code=tenant.code)


@router.post("/{token}/accept", response_model=TokenOut)
async def accept_invitation_endpoint(
    token: str,
    payload: InvitationAcceptRequest,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    result = await accept_invitation(
        token=token,
        password=payload.password,
        session=session,
        tenant=tenant,
    )
    if isinstance(result, JSONResponse):
        return result
    return result
