from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import auth, health, catalog, purchasing, stock, sales
from app.services.bootstrap import bootstrap_owner

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
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    await bootstrap_owner()


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
