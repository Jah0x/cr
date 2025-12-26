from fastapi import HTTPException, status

from app.repos.catalog_repo import CategoryRepo, BrandRepo, ProductLineRepo, ProductRepo


class CatalogService:
    def __init__(self, category_repo: CategoryRepo, brand_repo: BrandRepo, line_repo: ProductLineRepo, product_repo: ProductRepo):
        self.category_repo = category_repo
        self.brand_repo = brand_repo
        self.line_repo = line_repo
        self.product_repo = product_repo

    async def list_categories(self):
        return await self.category_repo.list()

    async def create_category(self, data):
        return await self.category_repo.create(data)

    async def update_category(self, category_id, data):
        category = await self.category_repo.get(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        for key, value in data.items():
            if value is not None:
                setattr(category, key, value)
        return category

    async def delete_category(self, category_id):
        category = await self.category_repo.get(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        await self.category_repo.delete(category)

    async def list_brands(self):
        return await self.brand_repo.list()

    async def create_brand(self, data):
        return await self.brand_repo.create(data)

    async def update_brand(self, brand_id, data):
        brand = await self.brand_repo.get(brand_id)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        for key, value in data.items():
            if value is not None:
                setattr(brand, key, value)
        return brand

    async def delete_brand(self, brand_id):
        brand = await self.brand_repo.get(brand_id)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        await self.brand_repo.delete(brand)

    async def list_lines(self, brand_id=None):
        return await self.line_repo.list(brand_id)

    async def create_line(self, data):
        return await self.line_repo.create(data)

    async def update_line(self, line_id, data):
        line = await self.line_repo.get(line_id)
        if not line:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Line not found")
        for key, value in data.items():
            if value is not None:
                setattr(line, key, value)
        return line

    async def delete_line(self, line_id):
        line = await self.line_repo.get(line_id)
        if not line:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Line not found")
        await self.line_repo.delete(line)

    async def list_products(self, filters):
        return await self.product_repo.list(filters)

    async def create_product(self, data):
        return await self.product_repo.create(data)

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
        return product

    async def delete_product(self, product_id):
        product = await self.product_repo.get(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        await self.product_repo.delete(product)
