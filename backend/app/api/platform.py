import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel, EmailStr

from app.core.config import get_settings
from app.core.deps import get_db_session, require_platform_auth, require_platform_host
from app.core.security import create_platform_token
from app.schemas.platform import (
    PlatformModuleCreate,
    PlatformModuleResponse,
    PlatformTemplateApply,
    PlatformTemplateCreate,
    PlatformTemplateResponse,
    PlatformTenantCreate,
    PlatformTenantCreateResponse,
    PlatformTenantDomainCreate,
    PlatformTenantDomainResponse,
    PlatformTenantInviteRequest,
    PlatformTenantInviteResponse,
    PlatformTenantResponse,
    PlatformTenantStatusResponse,
    PlatformTenantUpdate,
    PlatformTenantUpdateResponse,
    PlatformTenantUserCreate,
    PlatformTenantUserResponse,
    PlatformTenantUserUpdate,
)
from app.schemas.user import TokenOut
from app.services.platform_service import PlatformService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platform", tags=["platform"], dependencies=[Depends(require_platform_auth)])
auth_router = APIRouter(prefix="/platform/auth", tags=["platform"], dependencies=[Depends(require_platform_host)])


class PlatformLoginPayload(BaseModel):
    email: EmailStr
    password: str


@auth_router.post("/login", response_model=TokenOut)
async def login(payload: PlatformLoginPayload, session: AsyncSession = Depends(get_db_session)) -> TokenOut:
    settings = get_settings()
    if not settings.first_owner_email or not settings.first_owner_password:
        detail = "Platform auth not configured: missing FIRST_OWNER_EMAIL/FIRST_OWNER_PASSWORD"
        logger.error(detail)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
    row = (
        await session.execute(
            text(
                """
                select
                    to_regclass('public.users') as users,
                    to_regclass('public.roles') as roles,
                    to_regclass('public.user_roles') as user_roles
                """
            )
        )
    ).mappings().one()
    missing = [name for name, value in row.items() if value is None]
    if missing:
        detail = f"Platform auth not configured: missing public tables {', '.join(missing)}"
        logger.error(detail)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
    if payload.email != settings.first_owner_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if payload.password != settings.first_owner_password:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid password")
    token = create_platform_token(subject=payload.email, roles=["owner"])
    return TokenOut(access_token=token)


@router.get("/tenants", response_model=list[PlatformTenantResponse])
async def list_tenants(session: AsyncSession = Depends(get_db_session)):
    service = PlatformService(session)
    tenants = await service.list_tenants()
    return [
        PlatformTenantResponse(
            id=str(t.id),
            name=t.name,
            code=t.code,
            status=t.status.value,
            last_error=t.last_error,
        )
        for t in tenants
    ]


@router.post("/tenants", response_model=PlatformTenantCreateResponse)
async def create_tenant(payload: PlatformTenantCreate, session: AsyncSession = Depends(get_db_session)):
    service = PlatformService(session)
    result = await service.create_tenant(
        name=payload.name,
        code=payload.code,
        template_id=payload.template_id,
        owner_email=payload.owner_email,
    )
    tenant = result["tenant"]
    return PlatformTenantCreateResponse(
        id=str(tenant.id),
        name=tenant.name,
        code=tenant.code,
        status=tenant.status.value,
        tenant_url=result["tenant_url"],
        owner_email=result["owner_email"],
        invite_url=result["invite_url"],
    )


@router.patch("/tenants/{tenant_id}", response_model=PlatformTenantUpdateResponse)
async def update_tenant(
    tenant_id: str,
    payload: PlatformTenantUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    service = PlatformService(session)
    tenant = await service.update_tenant(tenant_id, name=payload.name, status=payload.status)
    return PlatformTenantUpdateResponse(
        id=str(tenant.id),
        name=tenant.name,
        code=tenant.code,
        status=tenant.status.value,
        last_error=tenant.last_error,
    )


@router.get("/tenants/{tenant_id}/status", response_model=PlatformTenantStatusResponse)
async def tenant_status(tenant_id: str, session: AsyncSession = Depends(get_db_session)):
    service = PlatformService(session)
    status_info = await service.get_tenant_status(tenant_id)
    tenant = status_info["tenant"]
    return PlatformTenantStatusResponse(
        id=str(tenant.id),
        name=tenant.name,
        code=tenant.code,
        status=tenant.status.value,
        last_error=tenant.last_error,
        schema=status_info["schema"],
        schema_exists=status_info["schema_exists"],
        revision=status_info["revision"],
        head_revision=status_info["head_revision"],
    )


@router.post("/tenants/{tenant_id}/migrate", response_model=PlatformTenantStatusResponse)
async def migrate_tenant(tenant_id: str, session: AsyncSession = Depends(get_db_session)):
    service = PlatformService(session)
    status_info = await service.migrate_tenant(tenant_id)
    tenant = status_info["tenant"]
    return PlatformTenantStatusResponse(
        id=str(tenant.id),
        name=tenant.name,
        code=tenant.code,
        status=tenant.status.value,
        last_error=tenant.last_error,
        schema=status_info["schema"],
        schema_exists=status_info["schema_exists"],
        revision=status_info["revision"],
        head_revision=status_info["head_revision"],
    )


@router.get("/tenants/{tenant_id}/domains", response_model=list[PlatformTenantDomainResponse])
async def list_domains(tenant_id: str, session: AsyncSession = Depends(get_db_session)):
    service = PlatformService(session)
    domains = await service.list_domains(tenant_id)
    return [
        PlatformTenantDomainResponse(
            id=str(domain.id),
            domain=domain.domain,
            is_primary=domain.is_primary,
            created_at=domain.created_at.isoformat(),
        )
        for domain in domains
    ]


@router.post("/tenants/{tenant_id}/domains", response_model=PlatformTenantDomainResponse)
async def create_domain(
    tenant_id: str,
    payload: PlatformTenantDomainCreate,
    session: AsyncSession = Depends(get_db_session),
):
    service = PlatformService(session)
    domain = await service.create_domain(tenant_id, payload.domain, payload.is_primary)
    return PlatformTenantDomainResponse(
        id=str(domain.id),
        domain=domain.domain,
        is_primary=domain.is_primary,
        created_at=domain.created_at.isoformat(),
    )


@router.delete("/tenants/{tenant_id}/domains/{domain_id}")
async def delete_domain(tenant_id: str, domain_id: str, session: AsyncSession = Depends(get_db_session)):
    service = PlatformService(session)
    await service.delete_domain(tenant_id, domain_id)
    return {"status": "deleted"}


@router.post("/tenants/{tenant_id}/invite", response_model=PlatformTenantInviteResponse)
async def create_invite(
    tenant_id: str,
    payload: PlatformTenantInviteRequest,
    session: AsyncSession = Depends(get_db_session),
):
    service = PlatformService(session)
    invite = await service.create_invite(tenant_id, payload.email, payload.role_name)
    return PlatformTenantInviteResponse(invite_url=invite["invite_url"], expires_at=invite["expires_at"])


@router.get("/tenants/{tenant_id}/users", response_model=list[PlatformTenantUserResponse])
async def list_users(tenant_id: str, session: AsyncSession = Depends(get_db_session)):
    service = PlatformService(session)
    users = await service.list_users(tenant_id)
    return [
        PlatformTenantUserResponse(
            id=str(user.id),
            email=user.email,
            roles=[role.name for role in user.roles],
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        )
        for user in users
    ]


@router.post("/tenants/{tenant_id}/users", response_model=PlatformTenantUserResponse)
async def create_user(
    tenant_id: str,
    payload: PlatformTenantUserCreate,
    session: AsyncSession = Depends(get_db_session),
):
    if not payload.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required")
    service = PlatformService(session)
    user = await service.create_user(tenant_id, payload.email, payload.password, payload.role_names)
    return PlatformTenantUserResponse(
        id=str(user.id),
        email=user.email,
        roles=[role.name for role in user.roles],
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
    )


@router.patch("/tenants/{tenant_id}/users/{user_id}", response_model=PlatformTenantUserResponse)
async def update_user(
    tenant_id: str,
    user_id: str,
    payload: PlatformTenantUserUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    service = PlatformService(session)
    user = await service.update_user(tenant_id, user_id, is_active=payload.is_active)
    return PlatformTenantUserResponse(
        id=str(user.id),
        email=user.email,
        roles=[role.name for role in user.roles],
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
    )


@router.delete("/tenants/{tenant_id}/users/{user_id}")
async def delete_user(tenant_id: str, user_id: str, session: AsyncSession = Depends(get_db_session)):
    service = PlatformService(session)
    await service.delete_user(tenant_id, user_id)
    return {"status": "deleted"}


@router.post("/tenants/{tenant_id}/apply-template", response_model=PlatformTenantResponse)
async def apply_template(
    tenant_id: str,
    payload: PlatformTemplateApply,
    session: AsyncSession = Depends(get_db_session),
):
    service = PlatformService(session)
    tenant = await service.apply_template(tenant_id, payload.template_id)
    return PlatformTenantResponse(id=str(tenant.id), name=tenant.name, code=tenant.code, status=tenant.status.value)


@router.get("/modules", response_model=list[PlatformModuleResponse])
async def list_modules(session: AsyncSession = Depends(get_db_session)):
    service = PlatformService(session)
    modules = await service.list_modules()
    return [
        PlatformModuleResponse(
            id=str(module.id),
            code=module.code,
            name=module.name,
            description=module.description,
            is_active=module.is_active,
        )
        for module in modules
    ]


@router.post("/modules", response_model=PlatformModuleResponse)
async def create_module(payload: PlatformModuleCreate, session: AsyncSession = Depends(get_db_session)):
    service = PlatformService(session)
    module = await service.create_module(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
    )
    return PlatformModuleResponse(
        id=str(module.id),
        code=module.code,
        name=module.name,
        description=module.description,
        is_active=module.is_active,
    )


@router.get("/templates", response_model=list[PlatformTemplateResponse])
async def list_templates(session: AsyncSession = Depends(get_db_session)):
    service = PlatformService(session)
    templates = await service.list_templates()
    return [
        PlatformTemplateResponse(
            id=str(template.id),
            name=template.name,
            description=template.description,
            module_codes=template.module_codes or [],
            feature_codes=template.feature_codes or [],
        )
        for template in templates
    ]


@router.post("/templates", response_model=PlatformTemplateResponse)
async def create_template(payload: PlatformTemplateCreate, session: AsyncSession = Depends(get_db_session)):
    service = PlatformService(session)
    template = await service.create_template(
        name=payload.name,
        description=payload.description,
        module_codes=payload.module_codes,
        feature_codes=payload.feature_codes,
    )
    return PlatformTemplateResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        module_codes=template.module_codes or [],
        feature_codes=template.feature_codes or [],
    )
