import os
import uuid
import asyncio
from decimal import Decimal
import pathlib
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test")
os.environ.setdefault("JWT_EXPIRES", "3600")

from app.core.db import Base
from app.models.user import User
from app.models.catalog import Product, Category, Brand
from app.repos.catalog_repo import ProductRepo
from app.repos.sales_repo import SaleRepo, SaleItemRepo
from app.repos.stock_repo import StockRepo, StockBatchRepo
from app.repos.cash_repo import CashReceiptRepo, CashRegisterRepo
from app.repos.payment_repo import PaymentRepo, RefundRepo
from app.repos.tenant_settings_repo import TenantSettingsRepo
from app.repos.shifts_repo import CashierShiftRepo
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
    category = Category(id=uuid.uuid4(), name="Category")
    brand = Brand(id=uuid.uuid4(), name="Brand")
    session.add_all([user, category, brand])
    await session.flush()
    product = Product(
        id=uuid.uuid4(),
        sku=f"SKU-{uuid.uuid4()}",
        name="Item",
        description="",
        category_id=category.id,
        brand_id=brand.id,
        unit="pcs",
        purchase_price=Decimal("10.00"),
        sell_price=Decimal("10.00"),
        tax_rate=Decimal("0"),
    )
    session.add(product)
    await session.flush()
    return user, product


def test_sale_creates_stock_movements_and_receipt():
    asyncio.run(reset_db())

    async def scenario():
        seed_session = TestSession()
        async with seed_session.begin():
            user, product = await seed_user_and_product(seed_session)
            stock_repo = StockRepo(seed_session)
            await stock_repo.record_move(
                {"product_id": product.id, "delta_qty": Decimal("5"), "reason": "purchase", "reference": "init"}
            )
        await seed_session.close()
        session = TestSession()
        service = SalesService(
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
            TenantSettingsRepo(session),
            CashierShiftRepo(session),
        )
        sale, _ = await service.create_sale(
            {"items": [{"product_id": product.id, "qty": Decimal("2"), "unit_price": Decimal("10.00")}], "currency": "USD"},
            user.id,
        )
        moves = await StockRepo(session).list_moves(product.id)
        receipts = await CashReceiptRepo(session).find_by_sale(sale.id)
        await session.close()
        return sale, moves, receipts

    sale, moves, receipts = asyncio.run(scenario())
    assert sale.total_amount == Decimal("20.00")
    assert any(move.delta_qty < 0 for move in moves)
    assert len(receipts) == 1


def test_void_sale_restores_stock():
    asyncio.run(reset_db())

    async def scenario():
        seed_session = TestSession()
        async with seed_session.begin():
            user, product = await seed_user_and_product(seed_session)
            stock_repo = StockRepo(seed_session)
            await stock_repo.record_move(
                {"product_id": product.id, "delta_qty": Decimal("3"), "reason": "purchase", "reference": "init2"}
            )
        await seed_session.close()
        session = TestSession()
        service = SalesService(
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
            TenantSettingsRepo(session),
            CashierShiftRepo(session),
        )
        sale, _ = await service.create_sale(
            {"items": [{"product_id": product.id, "qty": Decimal("1"), "unit_price": Decimal("5.00")}], "currency": "USD"},
            user.id,
        )
        on_hand_after_sale = await StockRepo(session).on_hand(product.id)
        await SalesService(
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
            TenantSettingsRepo(session),
            CashierShiftRepo(session),
        ).void_sale(sale.id, user.id)
        on_hand_after_void = await StockRepo(session).on_hand(product.id)
        await session.close()
        return on_hand_after_sale, on_hand_after_void

    on_hand_after_sale, on_hand_after_void = asyncio.run(scenario())
    assert on_hand_after_void > on_hand_after_sale
