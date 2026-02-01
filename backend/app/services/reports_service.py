from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.sql import Select

from app.models.purchasing import PurchaseInvoice, PurchaseStatus, PurchaseItem
from app.models.sales import Sale, SaleStatus, SaleItem, SaleTaxLine, PaymentProvider
from app.models.catalog import Product, Category, Brand
from app.models.stock import SaleItemCostAllocation, StockBatch, StockMove
from app.models.finance import Expense
from app.schemas.reports import SummaryReport, GroupReport, TopProductReport, PnlReport, TaxReportItem


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

    async def taxes(self, date_from: datetime | None = None, date_to: datetime | None = None, methods: list[str] | None = None):
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
        if methods:
            stmt = stmt.where(SaleTaxLine.method.in_(methods))

        result = await self.session.execute(stmt)
        method_keys = [method.value for method in PaymentProvider]
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
                method_value = method.value if isinstance(method, PaymentProvider) else str(method)
                if method_value in aggregated[rule_key]["by_method"]:
                    aggregated[rule_key]["by_method"][method_value] += total_tax

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
