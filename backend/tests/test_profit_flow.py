import os
import uuid
import asyncio
from decimal import Decimal
import pathlib
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test")
os.environ.setdefault("JWT_EXPIRES", "3600")

from app.core.db import Base
from app.models.catalog import Product
from app.models.stock import StockBatch, SaleItemCostAllocation
from app.models.user import User
from app.repos.catalog_repo import ProductRepo
from app.repos.cash_repo import CashReceiptRepo, CashRegisterRepo
from app.repos.payment_repo import PaymentRepo, RefundRepo
from app.repos.purchasing_repo import SupplierRepo, PurchaseInvoiceRepo, PurchaseItemRepo
from app.repos.sales_repo import SaleRepo, SaleItemRepo
from app.repos.stock_repo import StockRepo, StockBatchRepo
from app.services.purchasing_service import PurchasingService
from app.services.reports_service import ReportsService
from app.services.sales_service import SalesService

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


async def seed_user_and_product(session):
    user = User(
        email=f"user-{uuid.uuid4()}@example.com",
        password_hash="x",
        is_active=True,
    )
    product = Product(
        id=uuid.uuid4(),
        sku=f"SKU-{uuid.uuid4()}",
        name="Item",
        description="",
        price=Decimal("10.00"),
    )
    session.add_all([user, product])
    await session.flush()
    return user, product


def test_purchase_sale_cogs_pnl():
    asyncio.run(reset_db())

    async def scenario():
        session = TestSession()
        user, product = await seed_user_and_product(session)
        purchasing_service = PurchasingService(
            SupplierRepo(session),
            PurchaseInvoiceRepo(session),
            PurchaseItemRepo(session),
            StockRepo(session),
            StockBatchRepo(session),
            ProductRepo(session),
        )
        invoice = await purchasing_service.create_invoice({})
        await purchasing_service.add_item(
            invoice.id,
            {"product_id": product.id, "quantity": Decimal("10"), "unit_cost": Decimal("5.00")},
        )
        await purchasing_service.post_invoice(invoice.id)
        batch_result = await session.execute(
            select(StockBatch).where(StockBatch.product_id == product.id)
        )
        batch = batch_result.scalar_one()
        sales_service = SalesService(
            session,
            SaleRepo(session),
            SaleItemRepo(session),
            StockRepo(session),
            StockBatchRepo(session),
            ProductRepo(session),
            CashReceiptRepo(session),
            PaymentRepo(session),
            RefundRepo(session),
            CashRegisterRepo(session),
        )
        sale, _ = await sales_service.create_sale(
            {"items": [{"product_id": product.id, "qty": Decimal("3"), "unit_price": Decimal("10.00")}], "currency": "USD"},
            user.id,
        )
        await session.refresh(batch)
        allocations = await session.execute(
            select(SaleItemCostAllocation).where(SaleItemCostAllocation.sale_item_id == sale.items[0].id)
        )
        pnl = await ReportsService(session).pnl()
        await session.close()
        return batch, allocations.scalars().all(), pnl

    batch, allocations, pnl = asyncio.run(scenario())
    assert batch.quantity == Decimal("7")
    assert allocations
    assert pnl.cogs == Decimal("15.00")
