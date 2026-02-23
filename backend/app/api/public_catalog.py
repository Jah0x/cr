from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_tenant, get_db_session
from app.models.catalog import Brand, Category, Product, ProductLine
from app.models.platform import Module, TenantModule, TenantSettings
from app.models.public_order import PublicOrder, PublicOrderItem
from app.models.stock import StockMove
from app.schemas.public_catalog import (
    PublicCatalogOrderCreate,
    PublicCatalogOrderOut,
    PublicCatalogProductOut,
    PublicCatalogResponse,
)

router = APIRouter(prefix="/public/catalog", tags=["public-catalog"])


async def _catalog_enabled(session: AsyncSession, tenant_id) -> bool:
    public_catalog_module = await session.scalar(select(Module).where(Module.code == "public_catalog"))
    if not public_catalog_module or not public_catalog_module.is_active:
        return False
    tenant_module = await session.scalar(
        select(TenantModule).where(
            TenantModule.module_id == public_catalog_module.id,
            TenantModule.tenant_id == tenant_id,
        )
    )
    if not tenant_module or not tenant_module.is_enabled:
        return False
    tenant_settings = await session.get(TenantSettings, tenant_id)
    settings_payload = tenant_settings.settings if tenant_settings else {}
    catalog_settings = settings_payload.get("internet_catalog", {})
    return bool(catalog_settings.get("is_enabled", False))


@router.get("/products", response_model=PublicCatalogResponse)
async def list_public_catalog_products(
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
    q: str | None = Query(default=None),
):
    if not await _catalog_enabled(session, tenant.id):
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
            Product.variant_group,
            Product.variant_name,
            Category.name.label("category"),
            Brand.name.label("brand"),
            ProductLine.name.label("line"),
            on_hand_expr.label("on_hand"),
        )
        .join(Category, Category.id == Product.category_id)
        .join(Brand, Brand.id == Product.brand_id)
        .outerjoin(ProductLine, ProductLine.id == Product.line_id)
        .outerjoin(StockMove, StockMove.product_id == Product.id)
        .where(Product.is_active.is_(True), Product.is_hidden.is_(False))
        .group_by(
            Product.id,
            Product.name,
            Product.sku,
            Product.image_url,
            Product.unit,
            Product.sell_price,
            Product.variant_group,
            Product.variant_name,
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
            variant_group=row.variant_group,
            variant_name=row.variant_name,
        )
        for row in rows
    ]
    return PublicCatalogResponse(items=items)


@router.post('/orders', response_model=PublicCatalogOrderOut, status_code=status.HTTP_201_CREATED)
async def create_public_order(
    payload: PublicCatalogOrderCreate,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    if not await _catalog_enabled(session, tenant.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Catalog is disabled')

    product_ids = [item.product_id for item in payload.items]
    products = (
        (
            await session.execute(
                select(Product).where(Product.id.in_(product_ids), Product.is_active.is_(True), Product.is_hidden.is_(False))
            )
        )
        .scalars()
        .all()
    )
    product_map = {str(product.id): product for product in products}
    if len(product_map) != len(set(product_ids)):
        raise HTTPException(status_code=422, detail='Some products are unavailable')

    order = PublicOrder(
        customer_name=payload.customer_name.strip(),
        phone=payload.phone.strip(),
        comment=(payload.comment or '').strip() or None,
        status='new',
    )
    session.add(order)
    await session.flush()

    for item in payload.items:
        product = product_map[item.product_id]
        session.add(
            PublicOrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                qty=Decimal(str(item.qty)),
                unit_price=product.sell_price,
            )
        )

    await session.flush()
    return PublicCatalogOrderOut(id=str(order.id), status=order.status)
