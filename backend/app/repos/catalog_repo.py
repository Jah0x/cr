from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Category, Brand, ProductLine, Product


class CategoryRepo:
    def __init__(self, session: AsyncSession, tenant_id):
        self.session = session
        self.tenant_id = tenant_id

    async def list(self) -> List[Category]:
        result = await self.session.execute(select(Category).where(Category.tenant_id == self.tenant_id))
        return result.scalars().all()

    async def create(self, data: dict) -> Category:
        payload = {**data, "tenant_id": self.tenant_id}
        category = Category(**payload)
        self.session.add(category)
        await self.session.flush()
        return category

    async def get(self, category_id) -> Optional[Category]:
        result = await self.session.execute(
            select(Category).where(Category.id == category_id, Category.tenant_id == self.tenant_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, category: Category) -> None:
        await self.session.delete(category)


class BrandRepo:
    def __init__(self, session: AsyncSession, tenant_id):
        self.session = session
        self.tenant_id = tenant_id

    async def list(self) -> List[Brand]:
        result = await self.session.execute(select(Brand).where(Brand.tenant_id == self.tenant_id))
        return result.scalars().all()

    async def create(self, data: dict) -> Brand:
        payload = {**data, "tenant_id": self.tenant_id}
        brand = Brand(**payload)
        self.session.add(brand)
        await self.session.flush()
        return brand

    async def get(self, brand_id) -> Optional[Brand]:
        result = await self.session.execute(select(Brand).where(Brand.id == brand_id, Brand.tenant_id == self.tenant_id))
        return result.scalar_one_or_none()

    async def delete(self, brand: Brand) -> None:
        await self.session.delete(brand)


class ProductLineRepo:
    def __init__(self, session: AsyncSession, tenant_id):
        self.session = session
        self.tenant_id = tenant_id

    async def list(self, brand_id: Optional[str] = None) -> List[ProductLine]:
        stmt = select(ProductLine).where(ProductLine.tenant_id == self.tenant_id)
        if brand_id:
            stmt = stmt.where(ProductLine.brand_id == brand_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: dict) -> ProductLine:
        payload = {**data, "tenant_id": self.tenant_id}
        line = ProductLine(**payload)
        self.session.add(line)
        await self.session.flush()
        return line

    async def get(self, line_id) -> Optional[ProductLine]:
        result = await self.session.execute(
            select(ProductLine).where(ProductLine.id == line_id, ProductLine.tenant_id == self.tenant_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, line: ProductLine) -> None:
        await self.session.delete(line)


class ProductRepo:
    def __init__(self, session: AsyncSession, tenant_id):
        self.session = session
        self.tenant_id = tenant_id

    async def list(self, filters: dict) -> List[Product]:
        stmt = select(Product).where(Product.tenant_id == self.tenant_id)
        if filters.get("category_id"):
            stmt = stmt.where(Product.category_id == filters["category_id"])
        if filters.get("brand_id"):
            stmt = stmt.where(Product.brand_id == filters["brand_id"])
        if filters.get("line_id"):
            stmt = stmt.where(Product.line_id == filters["line_id"])
        if filters.get("is_active") is not None:
            stmt = stmt.where(Product.is_active == filters["is_active"])
        if filters.get("q"):
            stmt = stmt.where(Product.name.ilike(f"%{filters['q']}%"))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: dict) -> Product:
        payload = {**data, "tenant_id": self.tenant_id}
        product = Product(**payload)
        self.session.add(product)
        await self.session.flush()
        return product

    async def get(self, product_id) -> Optional[Product]:
        result = await self.session.execute(select(Product).where(Product.id == product_id, Product.tenant_id == self.tenant_id))
        return result.scalar_one_or_none()

    async def soft_delete(self, product: Product) -> None:
        product.is_active = False
        await self.session.flush()
