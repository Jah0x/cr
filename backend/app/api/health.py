import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session
from app.models.tenant import TenantStatus
from app.repos.tenant_repo import TenantRepo

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health():
    return {"status": "ok"}


@router.get("/z")
async def healthz():
    return {"status": "ok"}


def _tenant_indicator(request: Request, tenant: str | None):
    tenant_id = request.headers.get("x-tenant-id")
    if tenant_id:
        try:
            uuid.UUID(tenant_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tenant id")
        return ("id", tenant_id)
    tenant_code = request.headers.get("x-tenant-code") or request.headers.get("x-tenant")
    if tenant_code:
        return ("code", tenant_code)
    if tenant:
        try:
            uuid.UUID(tenant)
            return ("id", tenant)
        except ValueError:
            return ("code", tenant)
    return None


async def _assert_migrations(session: AsyncSession):
    try:
        await session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Migrations not applied")


async def readiness_check(session: AsyncSession, request: Request, tenant: str | None):
    indicator = _tenant_indicator(request, tenant)
    if not indicator:
        await session.execute(text("SELECT 1"))
        return {"status": "ready"}
    repo = TenantRepo(session)
    key, value = indicator
    tenant_obj = await repo.get_by_id(value) if key == "id" else await repo.get_by_code(value)
    if not tenant_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    if tenant_obj.status != TenantStatus.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant inactive")
    await session.execute(text("SELECT 1"))
    await _assert_migrations(session)
    return {"status": "ready"}


@router.get("/ready")
async def readyz(request: Request, tenant: str | None = None, session: AsyncSession = Depends(get_db_session)):
    return await readiness_check(session, request, tenant)
