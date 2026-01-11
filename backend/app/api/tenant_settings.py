from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_tenant, get_db_session, require_feature, require_roles
from app.schemas.tenant_settings import (
    TenantFeatureSetting,
    TenantFeatureUpdate,
    TenantModuleSetting,
    TenantModuleUpdate,
    TenantSettingsResponse,
    TenantUIPrefs,
    TenantUIPrefsUpdate,
)
from app.services.tenant_settings_service import TenantSettingsService

router = APIRouter(prefix="/tenant/settings", tags=["tenant-settings"])


def get_service(session: AsyncSession):
    return TenantSettingsService(session)


@router.get("", response_model=TenantSettingsResponse, dependencies=[Depends(require_roles({"owner"})), Depends(get_current_tenant)])
async def get_settings(session: AsyncSession = Depends(get_db_session), tenant=Depends(get_current_tenant)):
    return await get_service(session).get_settings()


@router.patch(
    "/modules/{code}",
    response_model=TenantModuleSetting,
    dependencies=[Depends(require_roles({"owner"})), Depends(get_current_tenant)],
)
async def update_module(
    code: str,
    payload: TenantModuleUpdate,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    return await get_service(session).update_module(code, payload.is_enabled)

@router.delete(
    "/modules/{code}",
    response_model=TenantModuleSetting,
    dependencies=[Depends(require_roles({"owner"})), Depends(get_current_tenant)],
)
async def delete_module(
    code: str,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    return await get_service(session).delete_module(code)


@router.patch(
    "/features/{code}",
    response_model=TenantFeatureSetting,
    dependencies=[Depends(require_roles({"owner"})), Depends(get_current_tenant)],
)
async def update_feature(
    code: str,
    payload: TenantFeatureUpdate,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    return await get_service(session).update_feature(code, payload.is_enabled)

@router.delete(
    "/features/{code}",
    response_model=TenantFeatureSetting,
    dependencies=[Depends(require_roles({"owner"})), Depends(get_current_tenant)],
)
async def delete_feature(
    code: str,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    return await get_service(session).delete_feature(code)


@router.put(
    "/ui-prefs",
    response_model=TenantUIPrefs,
    dependencies=[Depends(require_roles({"owner"})), Depends(get_current_tenant), Depends(require_feature("ui_prefs"))],
)
async def update_ui_prefs(
    payload: TenantUIPrefsUpdate,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    prefs = await get_service(session).update_ui_prefs(payload.prefs)
    return {"prefs": prefs}

@router.delete(
    "/ui-prefs",
    response_model=TenantUIPrefs,
    dependencies=[Depends(require_roles({"owner"})), Depends(get_current_tenant), Depends(require_feature("ui_prefs"))],
)
async def delete_ui_prefs(
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    prefs = await get_service(session).delete_ui_prefs()
    return {"prefs": prefs}
