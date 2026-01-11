from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session, require_platform_auth
from app.schemas.platform import (
    PlatformModuleCreate,
    PlatformModuleResponse,
    PlatformTemplateApply,
    PlatformTemplateCreate,
    PlatformTemplateResponse,
    PlatformTenantCreate,
    PlatformTenantCreateResponse,
    PlatformTenantResponse,
)
from app.services.platform_service import PlatformService

router = APIRouter(prefix="/platform", tags=["platform"], dependencies=[Depends(require_platform_auth)])


@router.get("/tenants", response_model=list[PlatformTenantResponse])
async def list_tenants(session: AsyncSession = Depends(get_db_session)):
    service = PlatformService(session)
    tenants = await service.list_tenants()
    return [
        PlatformTenantResponse(id=str(t.id), name=t.name, code=t.code, status=t.status.value) for t in tenants
    ]


@router.post("/tenants", response_model=PlatformTenantCreateResponse)
async def create_tenant(payload: PlatformTenantCreate, session: AsyncSession = Depends(get_db_session)):
    service = PlatformService(session)
    result = await service.create_tenant(
        name=payload.name,
        code=payload.code,
        template_id=payload.template_id,
        owner_email=payload.owner_email,
        owner_password=payload.owner_password,
    )
    tenant = result["tenant"]
    return PlatformTenantCreateResponse(
        id=str(tenant.id),
        name=tenant.name,
        code=tenant.code,
        status=tenant.status.value,
        tenant_url=result["tenant_url"],
        owner_email=result["owner_email"],
        owner_password=result["owner_password"],
    )


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
