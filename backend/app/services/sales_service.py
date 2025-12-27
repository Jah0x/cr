from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.sales import PaymentProvider, PaymentStatus, SaleStatus
from app.repos.sales_repo import SaleRepo, SaleItemRepo
from app.repos.stock_repo import StockRepo
from app.repos.catalog_repo import ProductRepo
from app.repos.cash_repo import CashReceiptRepo, CashRegisterRepo
from app.repos.payment_repo import PaymentRepo, RefundRepo
from app.services.cash_register import get_cash_register


class SalesService:
    def __init__(
        self,
        session: AsyncSession,
        sale_repo: SaleRepo,
        item_repo: SaleItemRepo,
        stock_repo: StockRepo,
        product_repo: ProductRepo,
        receipt_repo: CashReceiptRepo,
        payment_repo: PaymentRepo,
        refund_repo: RefundRepo,
        cash_register_repo: CashRegisterRepo,
    ):
        self.session = session
        self.sale_repo = sale_repo
        self.item_repo = item_repo
        self.stock_repo = stock_repo
        self.product_repo = product_repo
        self.receipt_repo = receipt_repo
        self.payment_repo = payment_repo
        self.refund_repo = refund_repo
        self.cash_register_repo = cash_register_repo

    async def create_sale(self, payload: dict, user_id):
        items = payload.get("items", [])
        currency = payload.get("currency", "")
        payments = payload.get("payments", [])
        cash_register_id = payload.get("cash_register_id")
        if not items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Items required")
        product_ids = [item["product_id"] for item in items]
        products = {str(p.id): p for p in await self._fetch_products(product_ids)}
        total_amount = Decimal("0")
        async with self.session.begin():
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
            await self._create_payments(sale.id, payments, currency)
            register = await self._resolve_cash_register(cash_register_id)
            receipt = await register.register_sale(sale.id)
        sale = await self.sale_repo.get(sale.id)
        return sale, receipt

    async def void_sale(self, sale_id, user_id):
        async with self.session.begin():
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
            register = await self._resolve_cash_register()
            await register.refund_sale(sale.id)
        return await self.sale_repo.get(sale.id)

    async def create_refund(self, sale_id, payload: dict, user_id):
        async with self.session.begin():
            sale = await self.sale_repo.get(sale_id)
            if not sale:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
            items_payload = payload.get("items") or []
            reason = payload.get("reason", "")
            amount = Decimal(payload.get("amount") or 0)
            calculated = Decimal("0")
            items_map = {str(item.id): item for item in sale.items}
            if items_payload:
                for item_data in items_payload:
                    item = items_map.get(str(item_data["sale_item_id"]))
                    if not item:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale item not found")
                    qty = Decimal(item_data["qty"])
                    if qty <= 0 or qty > item.qty:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid quantity")
                    line_refund = (item.line_total / item.qty) * qty
                    calculated += line_refund
                    await self.stock_repo.record_move(
                        {
                            "product_id": item.product_id,
                            "delta_qty": qty,
                            "reason": "refund",
                            "ref_id": sale.id,
                            "reference": str(sale.id),
                            "created_by_user_id": user_id,
                        }
                    )
            else:
                for item in sale.items:
                    await self.stock_repo.record_move(
                        {
                            "product_id": item.product_id,
                            "delta_qty": item.qty,
                            "reason": "refund",
                            "ref_id": sale.id,
                            "reference": str(sale.id),
                            "created_by_user_id": user_id,
                        }
                    )
                    calculated += item.line_total
            refund_amount = calculated if calculated > 0 else amount
            if refund_amount <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refund amount required")
            await self.refund_repo.create(sale.id, {"amount": refund_amount, "reason": reason, "created_by_user_id": user_id})
            register = await self._resolve_cash_register()
            await register.refund_sale(sale.id)
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

    async def _create_payments(self, sale_id, payments, currency):
        if not payments:
            return
        for payment in payments:
            amount = Decimal(payment["amount"])
            if amount <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment amount")
            method = PaymentProvider(payment.get("method", "cash"))
            status_value = payment.get("status") or PaymentStatus.confirmed.value
            status_enum = PaymentStatus(status_value)
            await self.payment_repo.create(
                sale_id,
                {
                    "amount": amount,
                    "currency": payment.get("currency", currency),
                    "method": method,
                    "status": status_enum,
                    "reference": payment.get("reference", ""),
                },
            )

    async def _resolve_cash_register(self, cash_register_id=None):
        register = None
        if cash_register_id:
            register = await self.cash_register_repo.get_by_id(cash_register_id)
        elif settings.default_cash_register_id:
            register = await self.cash_register_repo.get_by_id(settings.default_cash_register_id)
        if not register:
            active = await self.cash_register_repo.get_active()
            if active:
                register = active[0]
        return get_cash_register(self.receipt_repo, register)
