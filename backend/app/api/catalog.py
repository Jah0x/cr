import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session, get_current_tenant, require_roles, require_module
from app.schemas.catalog import (
    CategoryCreate,
    CategoryUpdate,
    CategoryOut,
    BrandCreate,
    BrandUpdate,
    BrandOut,
    ProductLineCreate,
    ProductLineUpdate,
    ProductLineOut,
    ProductCreate,
    ProductUpdate,
    ProductOut,
)
from app.schemas.catalog_hierarchy import (
    CatalogHierarchyResponse,
    CatalogNodeCreate,
    CatalogNodeOut,
    CatalogNodeUpdate,
)
from app.services.catalog_service import CatalogService
from app.repos.catalog_repo import CategoryRepo, BrandRepo, ProductLineRepo, ProductRepo, CategoryBrandRepo
from app.repos.catalog_nodes_repo import CatalogNodeRepo
from app.repos.tenant_settings_repo import TenantSettingsRepo
from app.services.catalog_hierarchy_service import CatalogHierarchyService

router = APIRouter(
    prefix="",
    tags=["catalog"],
    dependencies=[
        Depends(require_roles({"owner", "admin"})),
        Depends(get_current_tenant),
        Depends(require_module("catalog")),
    ],
)


def get_catalog_service(session: AsyncSession):
    return CatalogService(
        CategoryRepo(session),
        BrandRepo(session),
        ProductLineRepo(session),
        ProductRepo(session),
        CategoryBrandRepo(session),
    )


def get_catalog_hierarchy_service(session: AsyncSession):
    return CatalogHierarchyService(
        CatalogNodeRepo(session),
        TenantSettingsRepo(session),
    )


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_catalog_service(session)
    return await service.list_categories()


@router.get("/catalog/hierarchy", response_model=CatalogHierarchyResponse)
async def get_catalog_hierarchy(session: AsyncSession = Depends(get_db_session), tenant=Depends(get_current_tenant)):
    service = get_catalog_hierarchy_service(session)
    return await service.get_hierarchy(tenant.id)


@router.get("/catalog/nodes", response_model=list[CatalogNodeOut])
async def list_catalog_nodes(
    parent_id: uuid.UUID | None = None,
    level_code: str | None = None,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    service = get_catalog_hierarchy_service(session)
    return await service.list_nodes(parent_id=parent_id, level_code=level_code)


@router.post("/catalog/nodes", response_model=CatalogNodeOut)
async def create_catalog_node(
    payload: CatalogNodeCreate,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    service = get_catalog_hierarchy_service(session)
    return await service.create_node(payload.model_dump())


@router.patch("/catalog/nodes/{node_id}", response_model=CatalogNodeOut)
async def update_catalog_node(
    node_id: uuid.UUID,
    payload: CatalogNodeUpdate,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    service = get_catalog_hierarchy_service(session)
    return await service.update_node(node_id, payload.model_dump(exclude_unset=True))


@router.delete("/catalog/nodes/{node_id}")
async def delete_catalog_node(
    node_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    tenant=Depends(get_current_tenant),
):
    service = get_catalog_hierarchy_service(session)
    await service.delete_node(node_id)
    return {"detail": "deleted"}


@router.post("/categories", response_model=CategoryOut)
async def create_category(payload: CategoryCreate, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_catalog_service(session)
    return await service.create_category(payload.model_dump())


@router.patch("/categories/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: str, payload: CategoryUpdate, request: Request, session: AsyncSession = Depends(get_db_session)
):
    service = get_catalog_service(session)
    return await service.update_category(category_id, payload.model_dump())


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_catalog_service(session)
    await service.delete_category(category_id)
    return {"detail": "deleted"}


@router.get("/brands", response_model=list[BrandOut])
async def list_brands(
    request: Request,
    category_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    service = get_catalog_service(session)
    return await service.list_brands(category_id=category_id)


@router.post("/brands", response_model=BrandOut)
async def create_brand(payload: BrandCreate, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_catalog_service(session)
    return await service.create_brand(payload.model_dump())


@router.patch("/brands/{brand_id}", response_model=BrandOut)
async def update_brand(brand_id: str, payload: BrandUpdate, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_catalog_service(session)
    return await service.update_brand(brand_id, payload.model_dump())


@router.delete("/brands/{brand_id}")
async def delete_brand(brand_id: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_catalog_service(session)
    await service.delete_brand(brand_id)
    return {"detail": "deleted"}


@router.post("/categories/{category_id}/brands/{brand_id}")
async def link_category_brand(
    category_id: uuid.UUID,
    brand_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    service = get_catalog_service(session)
    await service.link_category_brand(category_id, brand_id)
    return {"detail": "linked"}


@router.delete("/categories/{category_id}/brands/{brand_id}")
async def unlink_category_brand(
    category_id: uuid.UUID,
    brand_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    service = get_catalog_service(session)
    await service.unlink_category_brand(category_id, brand_id)
    return {"detail": "deleted"}


@router.get("/categories/{category_id}/brands", response_model=list[BrandOut])
async def list_category_brands(
    category_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    service = get_catalog_service(session)
    return await service.list_category_brands(category_id)


@router.get("/lines", response_model=list[ProductLineOut])
async def list_lines(request: Request, brand_id: str | None = None, session: AsyncSession = Depends(get_db_session)):
    service = get_catalog_service(session)
    return await service.list_lines(brand_id)


@router.post("/lines", response_model=ProductLineOut)
async def create_line(payload: ProductLineCreate, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_catalog_service(session)
    return await service.create_line(payload.model_dump())


@router.patch("/lines/{line_id}", response_model=ProductLineOut)
async def update_line(line_id: str, payload: ProductLineUpdate, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_catalog_service(session)
    return await service.update_line(line_id, payload.model_dump())


@router.delete("/lines/{line_id}")
async def delete_line(line_id: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_catalog_service(session)
    await service.delete_line(line_id)
    return {"detail": "deleted"}


@router.get("/products", response_model=list[ProductOut])
async def list_products(
    request: Request,
    category_id: str | None = None,
    brand_id: str | None = None,
    line_id: str | None = None,
    q: str | None = None,
    is_active: bool | None = True,
    session: AsyncSession = Depends(get_db_session),
):
    service = get_catalog_service(session)
    filters = {"category_id": category_id, "brand_id": brand_id, "line_id": line_id, "q": q, "is_active": is_active}
    return await service.list_products(filters)


@router.post("/products", response_model=ProductOut)
async def create_product(payload: ProductCreate, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_catalog_service(session)
    return await service.create_product(payload.model_dump())


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(product_id: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_catalog_service(session)
    return await service.get_product(product_id)


@router.patch("/products/{product_id}", response_model=ProductOut)
async def update_product(product_id: str, payload: ProductUpdate, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_catalog_service(session)
    return await service.update_product(product_id, payload.model_dump())


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = get_catalog_service(session)
    await service.delete_product(product_id)
    return {"detail": "deleted"}
