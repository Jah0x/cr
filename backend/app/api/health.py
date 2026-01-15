import logging
import os

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


@router.get("")
async def health():
    return {"status": "ok"}


@router.get("/z")
async def healthz():
    return {"status": "ok"}


def get_ready_dsn() -> str:
    dsn = os.getenv("DATABASE_DSN")
    if dsn:
        return dsn

    url = os.environ["DATABASE_URL"]
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace("postgres+asyncpg://", "postgres://")
    return url


async def _check_db_connection() -> None:
    dsn = get_ready_dsn()
    if not (dsn.startswith("postgresql://") or dsn.startswith("postgres://")):
        return

    try:
        conn = await asyncpg.connect(dsn)
    except Exception as exc:
        logger.exception("Readiness database connection failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "reason": "db_connect_failed", "details": str(exc)},
        ) from exc
    else:
        await conn.close()


async def _assert_migrations(session: AsyncSession) -> None:
    result = await session.execute(
        text(
            """
            select
                to_regclass('public.alembic_version') as alembic_version,
                to_regclass('public.tenants') as tenants,
                to_regclass('public.modules') as modules
            """
        )
    )
    row = result.mappings().first()
    alembic_ok = row and row["alembic_version"]
    tenants_ok = row and row["tenants"]
    modules_ok = row and row["modules"]
    if not alembic_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "reason": "migrations_not_applied"},
        )
    if not tenants_ok or not modules_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "reason": "public_schema_not_initialized",
                "details": "public schema is not initialized (missing public.tenants/public.modules)",
            },
        )


async def readiness_check(_session: AsyncSession, _request: Request, _: object | None = None):
    await _check_db_connection()
    await _assert_migrations(_session)
    return {"status": "ready"}


@router.get("/ready")
async def readyz(request: Request, session: AsyncSession = Depends(get_db_session)):
    return await readiness_check(session, request)
