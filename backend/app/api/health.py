import logging
import os

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_utils import set_search_path
from app.core.deps import get_db_session

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)


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


async def readiness_check(session: AsyncSession, request: Request, _: object | None = None):
    await _check_db_connection()
    request.state.tenant = None
    request.state.tenant_schema = None
    await set_search_path(session, None)
    await session.execute(text("SELECT 1"))
    await _assert_migrations(session)
    return {"status": "ready"}


@router.get("/ready")
async def readyz(request: Request, session: AsyncSession = Depends(get_db_session)):
    return await readiness_check(session, request)
