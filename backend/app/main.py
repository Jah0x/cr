import logging

from fastapi import FastAPI, APIRouter, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_db_session
from app.api import auth, health, catalog, purchasing, stock, sales, users, platform, tenant_settings, reports, finance
from app.api.health import readiness_check
from app.services.bootstrap import ensure_platform_owner

logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title="Retail POS", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(catalog.router)
api_router.include_router(purchasing.router)
api_router.include_router(stock.router)
api_router.include_router(sales.router)
api_router.include_router(users.router)
api_router.include_router(platform.auth_router)
api_router.include_router(platform.router)
api_router.include_router(tenant_settings.router)
api_router.include_router(reports.router)
api_router.include_router(finance.router)
app.include_router(api_router)


@app.on_event("startup")
async def startup():
    settings = get_settings()
    logger.info(
        "Platform auth configured: %s",
        bool(settings.first_owner_email and settings.first_owner_password),
    )
    await ensure_platform_owner()


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz(request: Request, session: AsyncSession = Depends(get_db_session)):
    return await readiness_check(session, request)
