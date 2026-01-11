import uuid
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import verify_token
from app.repos.tenant_repo import TenantRepo
from app.repos.user_repo import UserRepo
from app.services.tenant_service import TenantService

auth_scheme = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncSession:
    async for session in get_session():
        yield session


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
        await session.execute(text("SET LOCAL search_path TO :schema, public"), {"schema": schema})
        request.state.tenant_schema = schema
        return tenant
    if allow_public:
        request.state.tenant_schema = "public"
        await session.execute(text("SET LOCAL search_path TO public"))
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
    user = await repo.get_by_id(user_uuid, tenant.id)
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


async def get_current_tenant(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    session: AsyncSession = Depends(get_db_session),
):
    tenant = await resolve_tenant_with_schema(request, session)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant not specified")
    return tenant
