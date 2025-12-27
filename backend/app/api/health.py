from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.deps import get_db_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health():
    return {"status": "ok"}


@router.get("/z")
async def healthz():
    return {"status": "ok"}


@router.get("/ready")
async def readyz(session: AsyncSession = Depends(get_db_session)):
    await session.execute(text("SELECT 1"))
    return {"status": "ready"}
