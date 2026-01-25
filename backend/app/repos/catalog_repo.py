from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Category, Brand, ProductLine, Product, CategoryBrand


class CategoryRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> List[Category]:
        result = await self.session.execute(select(Category))
        return result.scalars().all()

    async def create(self, data: dict) -> Category:
        category = Category(**data)
        self.session.add(category)
        await self.session.flush()
        return category

    async def get(self, category_id) -> Optional[Category]:
        result = await self.session.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    async def delete(self, category: Category) -> None:
        await self.session.delete(category)


class BrandRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, category_id: Optional[str] = None) -> List[Brand]:
        stmt = select(Brand)
        if category_id:
            stmt = (
                stmt.join(CategoryBrand, Brand.id == CategoryBrand.brand_id)
                .where(CategoryBrand.category_id == category_id)
            )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: dict) -> Brand:
        brand = Brand(**data)
        self.session.add(brand)
        await self.session.flush()
        return brand

    async def get(self, brand_id) -> Optional[Brand]:
        result = await self.session.execute(select(Brand).where(Brand.id == brand_id))
        return result.scalar_one_or_none()

    async def delete(self, brand: Brand) -> None:
        await self.session.delete(brand)


class ProductLineRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, brand_id: Optional[str] = None) -> List[ProductLine]:
        stmt = select(ProductLine)
        if brand_id:
            stmt = stmt.where(ProductLine.brand_id == brand_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: dict) -> ProductLine:
        line = ProductLine(**data)
        self.session.add(line)
        await self.session.flush()
        return line

    async def get(self, line_id) -> Optional[ProductLine]:
        result = await self.session.execute(select(ProductLine).where(ProductLine.id == line_id))
        return result.scalar_one_or_none()

    async def delete(self, line: ProductLine) -> None:
        await self.session.delete(line)


class ProductRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, filters: dict) -> List[Product]:
        stmt = select(Product)
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
        product = Product(**data)
        self.session.add(product)
        await self.session.flush()
        return product

    async def get(self, product_id) -> Optional[Product]:
        result = await self.session.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def soft_delete(self, product: Product) -> None:
        product.is_active = False
        await self.session.flush()


class CategoryBrandRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, category_id, brand_id) -> CategoryBrand:
        link = CategoryBrand(category_id=category_id, brand_id=brand_id)
        self.session.add(link)
        await self.session.flush()
        return link

    async def get(self, category_id, brand_id) -> Optional[CategoryBrand]:
        result = await self.session.execute(
            select(CategoryBrand).where(
                CategoryBrand.category_id == category_id,
                CategoryBrand.brand_id == brand_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, link: CategoryBrand) -> None:
        await self.session.delete(link)

    async def list_brands_for_category(self, category_id) -> List[Brand]:
        result = await self.session.execute(
            select(Brand)
            .join(CategoryBrand, Brand.id == CategoryBrand.brand_id)
            .where(CategoryBrand.category_id == category_id)
        )
        return result.scalars().all()
