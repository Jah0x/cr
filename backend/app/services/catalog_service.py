from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.repos.catalog_repo import CategoryRepo, BrandRepo, ProductLineRepo, ProductRepo, CategoryBrandRepo


class CatalogService:
    def __init__(
        self,
        category_repo: CategoryRepo,
        brand_repo: BrandRepo,
        line_repo: ProductLineRepo,
        product_repo: ProductRepo,
        category_brand_repo: CategoryBrandRepo,
    ):
        self.category_repo = category_repo
        self.brand_repo = brand_repo
        self.line_repo = line_repo
        self.product_repo = product_repo
        self.category_brand_repo = category_brand_repo
        self.session = category_repo.session

    async def list_categories(self):
        return await self.category_repo.list()

    async def create_category(self, data):
        try:
            category = await self.category_repo.create(data)
            await self.session.refresh(category)
            return category
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category already exists",
            ) from exc

    async def update_category(self, category_id, data):
        category = await self.category_repo.get(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        for key, value in data.items():
            if value is not None:
                setattr(category, key, value)
        try:
            await self.session.flush()
            await self.session.refresh(category)
            return category
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category already exists",
            ) from exc

    async def delete_category(self, category_id):
        category = await self.category_repo.get(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        await self.category_repo.delete(category)

    async def list_brands(self, category_id=None):
        if category_id:
            category = await self.category_repo.get(category_id)
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return await self.brand_repo.list(category_id=category_id)

    async def create_brand(self, data):
        try:
            brand = await self.brand_repo.create(data)
            await self.session.refresh(brand)
            return brand
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Brand already exists",
            ) from exc

    async def update_brand(self, brand_id, data):
        brand = await self.brand_repo.get(brand_id)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        for key, value in data.items():
            if value is not None:
                setattr(brand, key, value)
        try:
            await self.session.flush()
            await self.session.refresh(brand)
            return brand
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Brand already exists",
            ) from exc

    async def delete_brand(self, brand_id):
        brand = await self.brand_repo.get(brand_id)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        await self.brand_repo.delete(brand)

    async def list_category_brands(self, category_id):
        category = await self.category_repo.get(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return await self.category_brand_repo.list_brands_for_category(category_id)

    async def link_category_brand(self, category_id, brand_id):
        category = await self.category_repo.get(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        brand = await self.brand_repo.get(brand_id)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        try:
            await self.category_brand_repo.create(category_id, brand_id)
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category brand link already exists",
            ) from exc

    async def unlink_category_brand(self, category_id, brand_id):
        category = await self.category_repo.get(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        brand = await self.brand_repo.get(brand_id)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        link = await self.category_brand_repo.get(category_id, brand_id)
        if not link:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category brand link not found")
        await self.category_brand_repo.delete(link)

    async def list_lines(self, brand_id=None):
        return await self.line_repo.list(brand_id)

    async def create_line(self, data):
        try:
            line = await self.line_repo.create(data)
            await self.session.refresh(line)
            return line
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Line already exists",
            ) from exc

    async def update_line(self, line_id, data):
        line = await self.line_repo.get(line_id)
        if not line:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Line not found")
        for key, value in data.items():
            if value is not None:
                setattr(line, key, value)
        try:
            await self.session.flush()
            await self.session.refresh(line)
            return line
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Line already exists",
            ) from exc

    async def delete_line(self, line_id):
        line = await self.line_repo.get(line_id)
        if not line:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Line not found")
        await self.line_repo.delete(line)

    async def list_products(self, filters):
        return await self.product_repo.list(filters)

    async def create_product(self, data):
        try:
            product = await self.product_repo.create(data)
            await self.session.refresh(product)
            return product
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product already exists",
            ) from exc

    async def get_product(self, product_id):
        product = await self.product_repo.get(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    async def update_product(self, product_id, data):
        product = await self.product_repo.get(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        for key, value in data.items():
            if value is not None:
                setattr(product, key, value)
        try:
            await self.session.flush()
            await self.session.refresh(product)
            return product
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product already exists",
            ) from exc

    async def delete_product(self, product_id):
        product = await self.product_repo.get(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        await self.product_repo.soft_delete(product)
