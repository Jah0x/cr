from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_tenant, get_db_session
from app.models.catalog import Brand, Category, Product, ProductLine
from app.models.platform import TenantSettings
from app.models.stock import StockMove
from app.schemas.public_catalog import PublicCatalogProductOut, PublicCatalogResponse

router = APIRouter(prefix="/public/catalog", tags=["public-catalog"])


@router.get("/products", response_model=PublicCatalogResponse)
async def list_public_catalog_products(
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
    q: str | None = Query(default=None),
):
    tenant_settings = await session.get(TenantSettings, tenant.id)
    settings_payload = tenant_settings.settings if tenant_settings else {}
    catalog_settings = settings_payload.get("internet_catalog", {})
    if not bool(catalog_settings.get("is_enabled", False)):
        return PublicCatalogResponse(items=[])

    on_hand_expr = func.coalesce(func.sum(StockMove.delta_qty), 0)
    stmt = (
        select(
            Product.id,
            Product.name,
            Product.sku,
            Product.image_url,
            Product.unit,
            Product.sell_price,
            Category.name.label("category"),
            Brand.name.label("brand"),
            ProductLine.name.label("line"),
            on_hand_expr.label("on_hand"),
        )
        .join(Category, Category.id == Product.category_id)
        .join(Brand, Brand.id == Product.brand_id)
        .outerjoin(ProductLine, ProductLine.id == Product.line_id)
        .outerjoin(StockMove, StockMove.product_id == Product.id)
        .where(Product.is_active.is_(True))
        .group_by(
            Product.id,
            Product.name,
            Product.sku,
            Product.image_url,
            Product.unit,
            Product.sell_price,
            Category.name,
            Brand.name,
            ProductLine.name,
        )
        .order_by(func.lower(Product.name), Product.id)
    )
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))
    rows = (await session.execute(stmt)).all()
    items = [
        PublicCatalogProductOut(
            id=str(row.id),
            name=row.name,
            sku=row.sku,
            image_url=row.image_url,
            unit=row.unit.value if hasattr(row.unit, "value") else str(row.unit),
            sell_price=row.sell_price,
            category=row.category,
            brand=row.brand,
            line=row.line,
            on_hand=float(row.on_hand or 0),
        )
        for row in rows
    ]
    return PublicCatalogResponse(items=items)
