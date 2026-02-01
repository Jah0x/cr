import os
import uuid
import asyncio
import pathlib
import sys

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

from app.core.db import Base
from decimal import Decimal

from app.models.catalog import Category, Brand, ProductLine
from app.repos.catalog_repo import CategoryRepo, BrandRepo, ProductLineRepo, ProductRepo, CategoryBrandRepo
from app.services.catalog_service import CatalogService

engine = create_async_engine(os.environ["DATABASE_URL"], future=True)
TestSession = async_sessionmaker(engine, expire_on_commit=False)
from app.core import db as core_db
core_db.engine = engine
core_db.async_session = TestSession


async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


def setup_module():
    if os.path.exists("./test.db"):
        os.remove("./test.db")
    asyncio.run(reset_db())


def teardown_module():
    asyncio.run(engine.dispose())
    if os.path.exists("./test.db"):
        os.remove("./test.db")


async def seed_category_and_brands(session):
    category = Category(id=uuid.uuid4(), name="Category")
    brand = Brand(id=uuid.uuid4(), name="Brand A")
    brand_two = Brand(id=uuid.uuid4(), name="Brand B")
    session.add_all([category, brand, brand_two])
    await session.flush()
    return category, brand, brand_two


async def seed_category_brand_line(session):
    category = Category(id=uuid.uuid4(), name="Category")
    brand = Brand(id=uuid.uuid4(), name="Brand A")
    line = ProductLine(id=uuid.uuid4(), name="Line A", brand_id=brand.id)
    session.add_all([category, brand, line])
    await session.flush()
    return category, brand, line


def test_category_brand_link_unique_and_filter():
    asyncio.run(reset_db())

    async def scenario():
        session = TestSession()
        service = CatalogService(
            CategoryRepo(session),
            BrandRepo(session),
            ProductLineRepo(session),
            ProductRepo(session),
            CategoryBrandRepo(session),
        )
        async with session.begin():
            category, brand, brand_two = await seed_category_and_brands(session)
        async with session.begin():
            await service.link_category_brand(category.id, brand.id)
            brands_for_category = await service.list_category_brands(category.id)
            filtered_brands = await service.list_brands(category_id=category.id)
        duplicate_status = None
        try:
            async with session.begin():
                await service.link_category_brand(category.id, brand.id)
        except HTTPException as exc:
            duplicate_status = exc.status_code
        await session.close()
        return brands_for_category, filtered_brands, duplicate_status, brand, brand_two

    brands_for_category, filtered_brands, duplicate_status, brand, brand_two = asyncio.run(scenario())
    assert [item.id for item in brands_for_category] == [brand.id]
    assert [item.id for item in filtered_brands] == [brand.id]
    assert brand_two.id not in [item.id for item in filtered_brands]
    assert duplicate_status == 409


def test_category_brand_unlink():
    asyncio.run(reset_db())

    async def scenario():
        session = TestSession()
        service = CatalogService(
            CategoryRepo(session),
            BrandRepo(session),
            ProductLineRepo(session),
            ProductRepo(session),
            CategoryBrandRepo(session),
        )
        async with session.begin():
            category, brand, _ = await seed_category_and_brands(session)
        async with session.begin():
            await service.link_category_brand(category.id, brand.id)
        async with session.begin():
            await service.unlink_category_brand(category.id, brand.id)
            brands_for_category = await service.list_category_brands(category.id)
        await session.close()
        return brands_for_category

    brands_for_category = asyncio.run(scenario())
    assert brands_for_category == []


def test_product_name_fallback_from_line():
    asyncio.run(reset_db())

    async def scenario():
        session = TestSession()
        service = CatalogService(
            CategoryRepo(session),
            BrandRepo(session),
            ProductLineRepo(session),
            ProductRepo(session),
            CategoryBrandRepo(session),
        )
        async with session.begin():
            category, brand, line = await seed_category_brand_line(session)
        async with session.begin():
            await service.link_category_brand(category.id, brand.id)
            product = await service.create_product(
                {
                    "category_id": category.id,
                    "brand_id": brand.id,
                    "line_id": line.id,
                    "name": "",
                    "sku": None,
                    "barcode": None,
                    "image_url": None,
                    "unit": "pcs",
                    "purchase_price": Decimal("10.00"),
                    "sell_price": Decimal("15.00"),
                    "tax_rate": Decimal("0"),
                }
            )
        await session.close()
        return product, line

    product, line = asyncio.run(scenario())
    assert product.name == line.name


def test_product_name_required_without_line():
    asyncio.run(reset_db())

    async def scenario():
        session = TestSession()
        service = CatalogService(
            CategoryRepo(session),
            BrandRepo(session),
            ProductLineRepo(session),
            ProductRepo(session),
            CategoryBrandRepo(session),
        )
        async with session.begin():
            category, brand, _ = await seed_category_and_brands(session)
        async with session.begin():
            await service.link_category_brand(category.id, brand.id)
        error_status = None
        try:
            async with session.begin():
                await service.create_product(
                    {
                        "category_id": category.id,
                        "brand_id": brand.id,
                        "line_id": None,
                        "name": "",
                        "sku": None,
                        "barcode": None,
                        "image_url": None,
                        "unit": "pcs",
                        "purchase_price": Decimal("10.00"),
                        "sell_price": Decimal("15.00"),
                        "tax_rate": Decimal("0"),
                    }
                )
        except HTTPException as exc:
            error_status = exc.status_code
        await session.close()
        return error_status

    error_status = asyncio.run(scenario())
    assert error_status == 422
