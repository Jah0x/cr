from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sales import SaleStatus
from app.repos.sales_repo import SaleRepo, SaleItemRepo
from app.repos.stock_repo import StockRepo
from app.repos.catalog_repo import ProductRepo
from app.repos.cash_repo import CashReceiptRepo
from app.services.cash_register import get_cash_register


class SalesService:
    def __init__(self, session: AsyncSession, sale_repo: SaleRepo, item_repo: SaleItemRepo, stock_repo: StockRepo, product_repo: ProductRepo, receipt_repo: CashReceiptRepo):
        self.session = session
        self.sale_repo = sale_repo
        self.item_repo = item_repo
        self.stock_repo = stock_repo
        self.product_repo = product_repo
        self.receipt_repo = receipt_repo
        self.register = get_cash_register(receipt_repo)

    async def create_sale(self, payload: dict, user_id):
        items = payload.get("items", [])
        currency = payload.get("currency", "")
        if not items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Items required")
        product_ids = [item["product_id"] for item in items]
        products = {str(p.id): p for p in await self._fetch_products(product_ids)}
        total_amount = Decimal("0")
        async with self.session.begin_nested():
            sale = await self.sale_repo.create({"currency": currency, "created_by_user_id": user_id})
            for item in items:
                product = products.get(str(item["product_id"]))
                if not product:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
                qty = Decimal(item["qty"])
                unit_price = item.get("unit_price")
                if unit_price is None:
                    unit_price = product.price
                unit_price = Decimal(unit_price)
                if qty <= 0 or unit_price < 0:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item values")
                on_hand = await self.stock_repo.on_hand(product.id)
                if not on_hand >= float(qty):
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")
                line_total = qty * unit_price
                total_amount += line_total
                await self.item_repo.add(
                    sale.id,
                    {
                        "product_id": product.id,
                        "qty": qty,
                        "unit_price": unit_price,
                        "line_total": line_total,
                    },
                )
                await self.stock_repo.record_move(
                    {
                        "product_id": product.id,
                        "delta_qty": -qty,
                        "reason": "sale",
                        "ref_id": sale.id,
                        "reference": str(sale.id),
                        "created_by_user_id": user_id,
                    }
                )
            sale.total_amount = total_amount
            await self.session.flush()
            receipt = await self.register.sell(sale.id)
        sale = await self.sale_repo.get(sale.id)
        return sale, receipt

    async def void_sale(self, sale_id, user_id):
        async with self.session.begin_nested():
            sale = await self.sale_repo.get(sale_id)
            if not sale:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
            if sale.status == SaleStatus.void:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sale already void")
            for item in sale.items:
                await self.stock_repo.record_move(
                    {
                        "product_id": item.product_id,
                        "delta_qty": item.qty,
                        "reason": "void",
                        "ref_id": sale.id,
                        "reference": str(sale.id),
                        "created_by_user_id": user_id,
                    }
                )
            sale.status = SaleStatus.void
            await self.session.flush()
            await self.register.refund(sale.id)
        return await self.sale_repo.get(sale.id)

    async def list_sales(self, status_filter=None, date_from=None, date_to=None):
        return await self.sale_repo.list(status_filter, date_from, date_to)

    async def get_sale(self, sale_id):
        sale = await self.sale_repo.get(sale_id)
        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
        return sale

    async def _fetch_products(self, ids):
        products = []
        for pid in ids:
            product = await self.product_repo.get(pid)
            if product:
                products.append(product)
        return products
