from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session, resolve_tenant_with_schema

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health():
    return {"status": "ok"}


@router.get("/z")
async def healthz():
    return {"status": "ok"}


async def _assert_migrations(session: AsyncSession):
    try:
        await session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Migrations not applied")


async def readiness_check(session: AsyncSession, request: Request):
    await resolve_tenant_with_schema(request, session, allow_public=True)
    await session.execute(text("SELECT 1"))
    await _assert_migrations(session)
    return {"status": "ready"}


@router.get("/ready")
async def readyz(request: Request, session: AsyncSession = Depends(get_db_session)):
    return await readiness_check(session, request)
