import uuid
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.db_utils import set_search_path
from app.core.security import verify_token
from app.models.platform import Module, TenantFeature, TenantModule
from app.repos.tenant_repo import TenantRepo
from app.repos.user_repo import UserRepo
from app.core.config import settings
from app.services.tenant_service import TenantService

auth_scheme = HTTPBearer(auto_error=False)


async def get_db_session(request: Request | None = None) -> AsyncSession:
    async for session in get_session():
        try:
            if request:
                tenant_schema = getattr(request.state, "tenant_schema", None)
                if tenant_schema:
                    await set_search_path(session, tenant_schema)
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def resolve_tenant_with_schema(
    request: Request,
    session: AsyncSession,
    *,
    allow_public: bool = False,
):
    tenant_service = TenantService(TenantRepo(session))
    tenant = await tenant_service.resolve_tenant(request)
    if tenant:
        schema = tenant.code
        await set_search_path(session, schema)
        request.state.tenant_schema = schema
        return tenant
    if allow_public:
        await set_search_path(session, None)
    return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    session: AsyncSession = Depends(get_db_session),
):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = credentials.credentials
    try:
        payload = verify_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    tenant = await resolve_tenant_with_schema(request, session)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant not specified")
    tenant_claim = payload.get("tenant_id")
    if str(tenant.id) != str(tenant_claim):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    repo = UserRepo(session)
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await repo.get_by_id(user_uuid)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


def require_roles(allowed_roles: set[str]):
    async def _checker(current_user=Depends(get_current_user)):
        allowed = {role.lower() for role in allowed_roles}
        role_names = {role.name.lower() for role in current_user.roles}
        if not role_names.intersection(allowed):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return current_user

    return _checker


def require_module(code: str):
    async def _checker(
        tenant=Depends(get_current_tenant),
        session: AsyncSession = Depends(get_db_session),
    ):
        result = await session.execute(select(Module).where(Module.code == code))
        module = result.scalar_one_or_none()
        if not module:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Module disabled")
        if not module.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Module disabled")
        tenant_module = await session.scalar(select(TenantModule).where(TenantModule.module_id == module.id))
        if not tenant_module or not tenant_module.is_enabled:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Module disabled")
        return True

    return _checker


def require_feature(code: str):
    async def _checker(
        tenant=Depends(get_current_tenant),
        session: AsyncSession = Depends(get_db_session),
    ):
        tenant_feature = await session.scalar(select(TenantFeature).where(TenantFeature.code == code))
        if not tenant_feature or not tenant_feature.is_enabled:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Feature disabled")
        return True

    return _checker


async def get_current_tenant(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    session: AsyncSession = Depends(get_db_session),
):
    tenant = await resolve_tenant_with_schema(request, session)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant not specified")
    return tenant


async def require_platform_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    if not settings.bootstrap_token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Bootstrap token not configured")
    platform_hosts = {item.strip().lower() for item in settings.platform_hosts.split(",") if item.strip()}
    if platform_hosts:
        host = (request.headers.get("host") or "").split(":", 1)[0].lower()
        if host not in platform_hosts:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if credentials.credentials != settings.bootstrap_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return True
