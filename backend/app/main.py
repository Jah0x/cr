from fastapi import FastAPI, APIRouter, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_db_session
from app.api import auth, health, catalog, purchasing, stock, sales, users, platform, tenant_settings, reports
from app.api.health import readiness_check

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
api_router.include_router(platform.router)
api_router.include_router(tenant_settings.router)
api_router.include_router(reports.router)
app.include_router(api_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz(request: Request, session: AsyncSession = Depends(get_db_session)):
    return await readiness_check(session, request)
