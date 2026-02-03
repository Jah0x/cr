from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, func, case
from sqlalchemy.sql import Select

from app.models.purchasing import PurchaseInvoice, PurchaseStatus, PurchaseItem
from app.models.sales import Sale, SaleStatus, SaleItem, SaleTaxLine, PaymentProvider, Payment, PaymentStatus
from app.models.catalog import Product, Category, Brand
from app.models.stock import SaleItemCostAllocation, StockBatch, StockMove
from app.models.finance import Expense
from app.schemas.reports import (
    SummaryReport,
    GroupReport,
    TopProductReport,
    PnlReport,
    TaxReportItem,
    FinanceOverviewReport,
    TopProductPerformanceReport,
    InventoryValuationReport,
    InventoryValuationItem,
)
from app.repos.tenant_settings_repo import TenantSettingsRepo


class ReportsService:
    def __init__(self, session):
        self.session = session

    async def summary(self):
        sales_sum = await self.session.execute(
            select(func.coalesce(func.sum(Sale.total_amount), 0)).where(Sale.status == SaleStatus.completed)
        )
        purchases_sum = await self.session.execute(
            select(func.coalesce(func.sum(PurchaseItem.quantity * PurchaseItem.unit_cost), 0)).join(PurchaseInvoice).where(PurchaseInvoice.status == PurchaseStatus.posted)
        )
        cogs_sum = await self.session.execute(
            select(func.coalesce(func.sum(SaleItemCostAllocation.quantity * StockBatch.unit_cost), 0))
            .join(StockBatch, StockBatch.id == SaleItemCostAllocation.batch_id)
            .join(SaleItem, SaleItem.id == SaleItemCostAllocation.sale_item_id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(Sale.status == SaleStatus.completed)
        )
        sales_total = sales_sum.scalar_one()
        purchase_total = purchases_sum.scalar_one()
        cogs_total = cogs_sum.scalar_one()
        return SummaryReport(total_sales=sales_total, total_purchases=purchase_total, gross_margin=sales_total - cogs_total)

    async def pnl(self, date_from: datetime | None = None, date_to: datetime | None = None):
        sales_stmt = select(func.coalesce(func.sum(Sale.total_amount), 0)).where(Sale.status == SaleStatus.completed)
        cogs_stmt = (
            select(func.coalesce(func.sum(SaleItemCostAllocation.quantity * StockBatch.unit_cost), 0))
            .join(StockBatch, StockBatch.id == SaleItemCostAllocation.batch_id)
            .join(SaleItem, SaleItem.id == SaleItemCostAllocation.sale_item_id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(Sale.status == SaleStatus.completed)
        )
        expenses_stmt: Select = select(func.coalesce(func.sum(Expense.amount), 0))
        if date_from:
            sales_stmt = sales_stmt.where(Sale.created_at >= date_from)
            cogs_stmt = cogs_stmt.where(Sale.created_at >= date_from)
            expenses_stmt = expenses_stmt.where(Expense.occurred_at >= date_from)
        if date_to:
            sales_stmt = sales_stmt.where(Sale.created_at <= date_to)
            cogs_stmt = cogs_stmt.where(Sale.created_at <= date_to)
            expenses_stmt = expenses_stmt.where(Expense.occurred_at <= date_to)
        total_sales = (await self.session.execute(sales_stmt)).scalar_one()
        cogs_total = (await self.session.execute(cogs_stmt)).scalar_one()
        expenses_total = (await self.session.execute(expenses_stmt)).scalar_one()
        gross_profit = total_sales - cogs_total
        net_profit = gross_profit - expenses_total
        return PnlReport(
            total_sales=total_sales,
            cogs=cogs_total,
            gross_profit=gross_profit,
            expenses_total=expenses_total,
            net_profit=net_profit,
            date_from=date_from,
            date_to=date_to,
        )

    async def by_category(self):
        result = await self.session.execute(
            select(Category.name, func.coalesce(func.sum(SaleItem.line_total), 0))
            .join(Product, Product.category_id == Category.id)
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(Sale.status == SaleStatus.completed)
            .group_by(Category.name)
        )
        return [GroupReport(name=row[0], total=row[1]) for row in result.all()]

    async def by_brand(self):
        result = await self.session.execute(
            select(Brand.name, func.coalesce(func.sum(SaleItem.line_total), 0))
            .join(Product, Product.brand_id == Brand.id)
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(Sale.status == SaleStatus.completed)
            .group_by(Brand.name)
        )
        return [GroupReport(name=row[0], total=row[1]) for row in result.all()]

    async def top_products(self, limit: int = 5):
        result = await self.session.execute(
            select(Product.id, Product.name, func.coalesce(func.sum(SaleItem.qty), 0))
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(Sale.status == SaleStatus.completed)
            .group_by(Product.id, Product.name)
            .order_by(func.sum(SaleItem.qty).desc())
            .limit(limit)
        )
        return [TopProductReport(product_id=str(row[0]), name=row[1], total=row[2]) for row in result.all()]

    async def stock_alerts(self, threshold: float):
        on_hand = func.coalesce(func.sum(StockMove.delta_qty), 0)
        result = await self.session.execute(
            select(Product.id, Product.name, on_hand)
            .outerjoin(StockMove, StockMove.product_id == Product.id)
            .group_by(Product.id, Product.name)
            .having(on_hand <= threshold)
        )
        return [TopProductReport(product_id=str(row[0]), name=row[1], total=row[2]) for row in result.all()]

    async def taxes(
        self,
        tenant_id,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        methods: list[str] | None = None,
    ):
        stmt = (
            select(
                SaleTaxLine.rule_id,
                SaleTaxLine.rule_name,
                SaleTaxLine.rate,
                SaleTaxLine.method,
                func.coalesce(func.sum(SaleTaxLine.tax_amount), 0),
            )
            .join(Sale, Sale.id == SaleTaxLine.sale_id)
            .where(Sale.status == SaleStatus.completed)
            .group_by(SaleTaxLine.rule_id, SaleTaxLine.rule_name, SaleTaxLine.rate, SaleTaxLine.method)
        )
        if date_from:
            stmt = stmt.where(Sale.created_at >= date_from)
        if date_to:
            stmt = stmt.where(Sale.created_at <= date_to)
        method_keys = [method.value for method in PaymentProvider]
        if methods:
            normalized_methods = [
                PaymentProvider.normalize(method) if isinstance(method, str) else method
                for method in methods
            ]
            filtered_methods = [method for method in normalized_methods if method in method_keys]
            if filtered_methods:
                stmt = stmt.where(SaleTaxLine.method.in_(filtered_methods))

        result = await self.session.execute(stmt)
        aggregated: dict[str, dict] = {}
        for rule_id, rule_name, rate, method, total_tax in result.all():
            rule_key = str(rule_id)
            if rule_key not in aggregated:
                aggregated[rule_key] = {
                    "rule_id": rule_key,
                    "name": rule_name,
                    "rate": rate,
                    "total_tax": Decimal("0"),
                    "by_method": {key: Decimal("0") for key in method_keys},
                }
            aggregated[rule_key]["total_tax"] += total_tax
            if method:
                method_value = PaymentProvider.normalize(method) if isinstance(method, str) else None
                if isinstance(method, PaymentProvider):
                    method_value = method.value
                if method_value is None:
                    method_value = str(method)
                if method_value in aggregated[rule_key]["by_method"]:
                    aggregated[rule_key]["by_method"][method_value] += total_tax

        tenant_settings = await TenantSettingsRepo(self.session).get_or_create(tenant_id)
        taxes_config = (tenant_settings.settings or {}).get("taxes", {})
        rules = taxes_config.get("rules") if isinstance(taxes_config, dict) else None
        if isinstance(taxes_config, dict) and taxes_config.get("enabled") and isinstance(rules, list):
            for rule in rules:
                rule_id = rule.get("id")
                if not rule_id:
                    continue
                rule_key = str(rule_id)
                if rule_key in aggregated:
                    continue
                aggregated[rule_key] = {
                    "rule_id": rule_key,
                    "name": rule.get("name"),
                    "rate": rule.get("rate"),
                    "total_tax": Decimal("0"),
                    "by_method": {key: Decimal("0") for key in method_keys},
                }

        return [
            TaxReportItem(
                rule_id=value["rule_id"],
                name=value["name"],
                rate=value["rate"],
                total_tax=value["total_tax"],
                by_method=value["by_method"],
            )
            for value in aggregated.values()
        ]

    async def finance_overview(self, date_from: datetime | None = None, date_to: datetime | None = None):
        revenue_stmt = select(func.coalesce(func.sum(Sale.total_amount), 0)).where(Sale.status == SaleStatus.completed)
        cogs_stmt = (
            select(func.coalesce(func.sum(SaleItemCostAllocation.quantity * StockBatch.unit_cost), 0))
            .join(StockBatch, StockBatch.id == SaleItemCostAllocation.batch_id)
            .join(SaleItem, SaleItem.id == SaleItemCostAllocation.sale_item_id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(Sale.status == SaleStatus.completed)
        )
        tax_stmt = (
            select(func.coalesce(func.sum(SaleTaxLine.tax_amount), 0))
            .join(Sale, Sale.id == SaleTaxLine.sale_id)
            .where(Sale.status == SaleStatus.completed)
        )
        payments_stmt = (
            select(Payment.method, func.coalesce(func.sum(Payment.amount), 0))
            .join(Sale, Sale.id == Payment.sale_id)
            .where(Sale.status == SaleStatus.completed, Payment.status == PaymentStatus.confirmed)
            .group_by(Payment.method)
        )
        taxes_by_method_stmt = (
            select(SaleTaxLine.method, func.coalesce(func.sum(SaleTaxLine.tax_amount), 0))
            .join(Sale, Sale.id == SaleTaxLine.sale_id)
            .where(Sale.status == SaleStatus.completed)
            .group_by(SaleTaxLine.method)
        )
        if date_from:
            revenue_stmt = revenue_stmt.where(Sale.created_at >= date_from)
            cogs_stmt = cogs_stmt.where(Sale.created_at >= date_from)
            tax_stmt = tax_stmt.where(Sale.created_at >= date_from)
            payments_stmt = payments_stmt.where(Sale.created_at >= date_from)
            taxes_by_method_stmt = taxes_by_method_stmt.where(Sale.created_at >= date_from)
        if date_to:
            revenue_stmt = revenue_stmt.where(Sale.created_at <= date_to)
            cogs_stmt = cogs_stmt.where(Sale.created_at <= date_to)
            tax_stmt = tax_stmt.where(Sale.created_at <= date_to)
            payments_stmt = payments_stmt.where(Sale.created_at <= date_to)
            taxes_by_method_stmt = taxes_by_method_stmt.where(Sale.created_at <= date_to)

        total_revenue = (await self.session.execute(revenue_stmt)).scalar_one()
        cogs_total = (await self.session.execute(cogs_stmt)).scalar_one()
        total_taxes = (await self.session.execute(tax_stmt)).scalar_one()
        gross_profit = total_revenue - cogs_total

        method_keys = [method.value for method in PaymentProvider]
        revenue_by_method = {key: Decimal("0") for key in method_keys}
        taxes_by_method = {key: Decimal("0") for key in method_keys}

        for method, total in (await self.session.execute(payments_stmt)).all():
            method_value = PaymentProvider.normalize(method) if isinstance(method, str) else None
            if isinstance(method, PaymentProvider):
                method_value = method.value
            if method_value in revenue_by_method:
                revenue_by_method[method_value] += total

        for method, total in (await self.session.execute(taxes_by_method_stmt)).all():
            if method is None:
                continue
            method_value = PaymentProvider.normalize(method) if isinstance(method, str) else None
            if isinstance(method, PaymentProvider):
                method_value = method.value
            if method_value in taxes_by_method:
                taxes_by_method[method_value] += total

        return FinanceOverviewReport(
            total_revenue=total_revenue,
            gross_profit=gross_profit,
            total_taxes=total_taxes,
            revenue_by_method=revenue_by_method,
            taxes_by_method=taxes_by_method,
        )

    async def top_products_performance(
        self,
        sort_by: str = "revenue",
        limit: int = 5,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ):
        sort_key = "revenue" if sort_by not in {"revenue", "margin"} else sort_by
        revenue_sum = func.coalesce(func.sum(SaleItem.line_total), 0)
        margin_sum = func.coalesce(func.sum(SaleItem.profit_line), 0)
        qty_sum = func.coalesce(func.sum(SaleItem.qty), 0)
        stmt = (
            select(Product.id, Product.name, qty_sum, revenue_sum, margin_sum)
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(Sale.status == SaleStatus.completed)
            .group_by(Product.id, Product.name)
        )
        if date_from:
            stmt = stmt.where(Sale.created_at >= date_from)
        if date_to:
            stmt = stmt.where(Sale.created_at <= date_to)
        order_metric = revenue_sum if sort_key == "revenue" else margin_sum
        stmt = stmt.order_by(order_metric.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return [
            TopProductPerformanceReport(
                product_id=str(row[0]),
                name=row[1],
                qty=row[2],
                revenue=row[3],
                margin=row[4],
            )
            for row in result.all()
        ]

    async def inventory_valuation(self):
        on_hand = func.coalesce(func.sum(StockMove.delta_qty), 0)
        unit_cost = case((Product.cost_price > 0, Product.cost_price), else_=Product.purchase_price)
        result = await self.session.execute(
            select(
                Product.id,
                Product.name,
                on_hand,
                unit_cost,
                (on_hand * unit_cost).label("total_value"),
            )
            .outerjoin(StockMove, StockMove.product_id == Product.id)
            .group_by(Product.id, Product.name, unit_cost)
        )
        items = []
        total_value = Decimal("0")
        for product_id, name, qty_on_hand, unit_cost, item_total in result.all():
            qty_on_hand = Decimal(qty_on_hand or 0)
            unit_cost = Decimal(unit_cost or 0)
            item_total = Decimal(item_total or 0)
            total_value += item_total
            items.append(
                InventoryValuationItem(
                    product_id=str(product_id),
                    name=name,
                    qty_on_hand=qty_on_hand,
                    unit_cost=unit_cost,
                    total_value=item_total,
                )
            )
        return InventoryValuationReport(total_value=total_value, items=items)
