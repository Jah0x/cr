from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.sales import PaymentProvider, PaymentStatus, SaleStatus, SaleTaxLine
from app.models.stock import SaleItemCostAllocation
from app.repos.sales_repo import SaleRepo, SaleItemRepo
from app.repos.stock_repo import StockRepo, StockBatchRepo
from app.repos.catalog_repo import ProductRepo
from app.repos.cash_repo import CashReceiptRepo, CashRegisterRepo
from app.repos.payment_repo import PaymentRepo, RefundRepo
from app.repos.tenant_settings_repo import TenantSettingsRepo
from app.services.cash_register import get_cash_register
from app.services.tax_service import calculate_sale_tax_lines
from app.repos.store_repo import StoreRepo


class SalesService:
    def __init__(
        self,
        session: AsyncSession,
        sale_repo: SaleRepo,
        item_repo: SaleItemRepo,
        stock_repo: StockRepo,
        batch_repo: StockBatchRepo,
        product_repo: ProductRepo,
        receipt_repo: CashReceiptRepo,
        payment_repo: PaymentRepo,
        refund_repo: RefundRepo,
        cash_register_repo: CashRegisterRepo,
        tenant_settings_repo: TenantSettingsRepo,
    ):
        self.session = session
        self.sale_repo = sale_repo
        self.item_repo = item_repo
        self.stock_repo = stock_repo
        self.batch_repo = batch_repo
        self.product_repo = product_repo
        self.receipt_repo = receipt_repo
        self.payment_repo = payment_repo
        self.refund_repo = refund_repo
        self.cash_register_repo = cash_register_repo
        self.tenant_settings_repo = tenant_settings_repo
        self.store_repo = StoreRepo(session)

    def _resolve_effective_cost(self, product):
        purchase_price = Decimal(product.purchase_price or 0)
        if purchase_price > 0:
            return purchase_price
        return Decimal(product.cost_price or 0)

    async def create_sale(self, payload: dict, user_id=None, tenant_id: str | None = None):
        items = payload.get("items", [])
        currency = (payload.get("currency") or "").strip()
        payments = payload.get("payments", [])
        cash_register_id = payload.get("cash_register_id")
        send_to_terminal = bool(payload.get("send_to_terminal", False))
        store_id = payload.get("store_id")
        if not store_id:
            store_id = (await self.store_repo.get_default()).id
        if not items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Items required")
        if not currency:
            currency = await self._resolve_currency(tenant_id)
        product_ids = [item["product_id"] for item in items]
        products = {str(p.id): p for p in await self._fetch_products(product_ids)}
        total_amount = Decimal("0")
        sale = await self.sale_repo.create(
            {
                "currency": currency,
                "created_by_user_id": user_id,
                "status": SaleStatus.draft,
                "send_to_terminal": send_to_terminal,
                "store_id": store_id,
            }
        )
        for item in items:
            product = products.get(str(item["product_id"]))
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            qty = Decimal(item["qty"])
            unit_price = item.get("unit_price")
            if unit_price is None:
                unit_price = product.sell_price
            unit_price = Decimal(unit_price)
            if qty <= 0 or unit_price < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item values")
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
        sale.total_amount = total_amount
        await self.session.flush()
        sale = await self.complete_sale(sale.id, payload, user_id, tenant_id)
        return sale, None

    async def create_draft_sale(self, payload: dict, user_id=None, tenant_id: str | None = None):
        currency = (payload.get("currency") or "").strip()
        send_to_terminal = bool(payload.get("send_to_terminal", False))
        store_id = payload.get("store_id")
        if not store_id:
            store_id = (await self.store_repo.get_default()).id
        if not currency:
            currency = await self._resolve_currency(tenant_id)
        sale = await self.sale_repo.create(
            {
                "currency": currency,
                "created_by_user_id": user_id,
                "status": SaleStatus.draft,
                "send_to_terminal": send_to_terminal,
                "store_id": store_id,
            }
        )
        return await self.sale_repo.get(sale.id)

    async def update_draft_sale_items(self, sale_id, payload: dict, tenant_id: str | None = None):
        items = payload.get("items") or []
        currency = (payload.get("currency") or "").strip()
        send_to_terminal = payload.get("send_to_terminal")
        store_id = payload.get("store_id")
        sale = await self.sale_repo.get(sale_id)
        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
        if sale.status != SaleStatus.draft:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sale is not draft")
        for existing_item in sale.items:
            await self.session.delete(existing_item)
        if currency:
            sale.currency = currency
        elif not sale.currency:
            sale.currency = await self._resolve_currency(tenant_id)
        if send_to_terminal is not None:
            sale.send_to_terminal = bool(send_to_terminal)
        if store_id:
            sale.store_id = store_id
        total_amount = Decimal("0")
        if items:
            product_ids = [item["product_id"] for item in items]
            products = {str(p.id): p for p in await self._fetch_products(product_ids)}
            for item in items:
                product = products.get(str(item["product_id"]))
                if not product:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
                qty = Decimal(item["qty"])
                unit_price = item.get("unit_price")
                if unit_price is None:
                    unit_price = product.sell_price
                unit_price = Decimal(unit_price)
                if qty <= 0 or unit_price < 0:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item values")
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
        sale.total_amount = total_amount
        await self.session.flush()
        return await self.sale_repo.get(sale.id)

    async def complete_sale(self, sale_id, payload: dict, user_id=None, tenant_id: str | None = None):
        settings = get_settings()
        payments = payload.get("payments", [])
        cash_register_id = payload.get("cash_register_id")
        sale = await self.sale_repo.get(sale_id)
        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
        if sale.status != SaleStatus.draft:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sale is not draft")
        if not sale.items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Items required")
        total_amount = Decimal("0")
        for item in sale.items:
            if not item.product_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            product = await self.product_repo.get(item.product_id)
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
            qty = Decimal(item.qty)
            unit_price = Decimal(item.unit_price)
            if qty <= 0 or unit_price < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid item values")
            on_hand = await self.stock_repo.on_hand(product.id)
            if not on_hand >= float(qty) and not settings.allow_negative_stock:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")
            line_total = qty * unit_price
            total_amount += line_total
            cost_snapshot = self._resolve_effective_cost(product)
            item.cost_snapshot = cost_snapshot
            item.profit_line = line_total - (cost_snapshot * qty)
            for allocation in item.allocations:
                await self.session.delete(allocation)
            consumed, remaining = await self.batch_repo.consume_with_fallback(product.id, float(qty))
            if remaining > 0:
                remaining_decimal = Decimal(str(remaining))
                fallback_cost = self._resolve_effective_cost(product)
                fallback_batch = await self.batch_repo.create(
                    {
                        "product_id": product.id,
                        "quantity": remaining_decimal,
                        "unit_cost": fallback_cost,
                    }
                )
                fallback_batch.quantity = Decimal("0")
                consumed.append((fallback_batch, remaining))
            for batch, consumed_qty in consumed:
                allocation = SaleItemCostAllocation(
                    sale_item_id=item.id,
                    batch_id=batch.id,
                    quantity=Decimal(str(consumed_qty)),
                )
                self.session.add(allocation)
            await self.stock_repo.record_move(
                {
                    "product_id": product.id,
                    "delta_qty": -qty,
                    "reason": "sale",
                    "ref_id": sale.id,
                    "reference": str(sale.id),
                    "created_by_user_id": user_id,
                    "store_id": sale.store_id,
                }
            )
        sale.total_amount = total_amount
        sale.status = SaleStatus.completed
        await self.session.flush()
        await self._create_sale_tax_lines(sale.id, total_amount, payments, tenant_id, sale.status)
        await self._create_payments(sale.id, payments, sale.currency or await self._resolve_currency(tenant_id))
        register = await self._resolve_cash_register(cash_register_id)
        await register.register_sale(sale.id)
        return await self.sale_repo.get(sale.id)

    async def cancel_sale(self, sale_id):
        sale = await self.sale_repo.get(sale_id)
        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
        if sale.status != SaleStatus.draft:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sale is not draft")
        sale.status = SaleStatus.cancelled
        await self.session.flush()
        return await self.sale_repo.get(sale.id)

    async def void_sale(self, sale_id, user_id):
        sale = await self.sale_repo.get(sale_id)
        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
        if sale.status == SaleStatus.cancelled:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sale already cancelled")
        for item in sale.items:
            await self._restore_batches(item, item.qty)
            await self.stock_repo.record_move(
                {
                    "product_id": item.product_id,
                    "delta_qty": item.qty,
                    "reason": "void",
                    "ref_id": sale.id,
                    "reference": str(sale.id),
                    "created_by_user_id": user_id,
                    "store_id": sale.store_id,
                }
            )
        sale.status = SaleStatus.cancelled
        await self.session.flush()
        register = await self._resolve_cash_register()
        await register.refund_sale(sale.id)
        return await self.sale_repo.get(sale.id)

    async def create_refund(self, sale_id, payload: dict, user_id):
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
                await self._restore_batches(item, qty)
                await self.stock_repo.record_move(
                    {
                        "product_id": item.product_id,
                        "delta_qty": qty,
                        "reason": "refund",
                        "ref_id": sale.id,
                        "reference": str(sale.id),
                        "created_by_user_id": user_id,
                        "store_id": sale.store_id,
                    }
                )
        else:
            for item in sale.items:
                await self._restore_batches(item, item.qty)
                await self.stock_repo.record_move(
                    {
                        "product_id": item.product_id,
                        "delta_qty": item.qty,
                        "reason": "refund",
                        "ref_id": sale.id,
                        "reference": str(sale.id),
                        "created_by_user_id": user_id,
                        "store_id": sale.store_id,
                    }
                )
                calculated += item.line_total
        refund_amount = calculated if calculated > 0 else amount
        if refund_amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refund amount required")
        await self.refund_repo.create(
            sale.id,
            {"amount": refund_amount, "reason": reason, "created_by_user_id": user_id},
        )
        register = await self._resolve_cash_register()
        await register.refund_sale(sale.id)
        return await self.sale_repo.get(sale.id)

    async def list_sales(self, status_filter=None, date_from=None, date_to=None, cashier_id=None, payment_method=None):
        return await self.sale_repo.list(
            status_filter,
            date_from,
            date_to,
            cashier_id=cashier_id,
            payment_method=payment_method,
        )

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

    async def _create_sale_tax_lines(self, sale_id, subtotal, payments, tenant_id, status):
        if status != SaleStatus.completed:
            return
        if not tenant_id:
            return
        settings_row = await self.tenant_settings_repo.get_or_create(tenant_id)
        tax_settings = (settings_row.settings or {}).get("taxes") if settings_row else None
        lines = calculate_sale_tax_lines(Decimal(subtotal), payments, tax_settings)
        if not lines:
            return
        for line in lines:
            self.session.add(
                SaleTaxLine(
                    sale_id=sale_id,
                    rule_id=line["rule_id"],
                    rule_name=line["rule_name"],
                    rate=line["rate"],
                    method=PaymentProvider(line["method"]) if line["method"] else None,
                    taxable_amount=line["taxable_amount"],
                    tax_amount=line["tax_amount"],
                )
            )
        await self.session.flush()

    async def _resolve_cash_register(self, cash_register_id=None):
        settings = get_settings()
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

    async def _resolve_currency(self, tenant_id: str | None) -> str:
        if tenant_id:
            settings_row = await self.tenant_settings_repo.get_or_create(tenant_id)
            currency = (settings_row.settings or {}).get("currency")
            if isinstance(currency, str) and currency.strip():
                return currency
        return "RUB"

    async def _restore_batches(self, sale_item, qty: Decimal):
        if not sale_item.product_id:
            return
        qty = Decimal(qty)
        if qty <= 0:
            return
        if sale_item.allocations:
            ratio = qty / sale_item.qty if sale_item.qty else Decimal("0")
            for allocation in sale_item.allocations:
                restore_qty = Decimal(allocation.quantity) * ratio
                if allocation.batch:
                    allocation.batch.quantity = Decimal(allocation.batch.quantity) + restore_qty
        else:
            product = await self.product_repo.get(sale_item.product_id)
            unit_cost = self._resolve_effective_cost(product) if product else Decimal("0")
            await self.batch_repo.create(
                {
                    "product_id": sale_item.product_id,
                    "quantity": qty,
                    "unit_cost": unit_cost,
                }
            )
