from sqlalchemy import select, func

from app.models.purchasing import PurchaseInvoice, PurchaseStatus, PurchaseItem
from app.models.sales import Sale, SaleStatus, SaleItem
from app.models.catalog import Product, Category, Brand
from app.schemas.reports import SummaryReport, GroupReport, TopProductReport


class ReportsService:
    def __init__(self, session):
        self.session = session

    async def summary(self):
        sales_sum = await self.session.execute(
            select(func.coalesce(func.sum(SaleItem.quantity * SaleItem.unit_price - SaleItem.discount_amount), 0)).join(Sale).where(Sale.status == SaleStatus.finalized)
        )
        purchases_sum = await self.session.execute(
            select(func.coalesce(func.sum(PurchaseItem.quantity * PurchaseItem.unit_cost), 0)).join(PurchaseInvoice).where(PurchaseInvoice.status == PurchaseStatus.posted)
        )
        sales_total = sales_sum.scalar_one()
        purchase_total = purchases_sum.scalar_one()
        return SummaryReport(total_sales=sales_total, total_purchases=purchase_total, gross_margin=sales_total - purchase_total)

    async def by_category(self):
        result = await self.session.execute(
            select(Category.name, func.coalesce(func.sum(SaleItem.quantity * SaleItem.unit_price), 0))
            .join(Product, Product.category_id == Category.id)
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale)
            .where(Sale.status == SaleStatus.finalized)
            .group_by(Category.name)
        )
        return [GroupReport(name=row[0], total=row[1]) for row in result.all()]

    async def by_brand(self):
        result = await self.session.execute(
            select(Brand.name, func.coalesce(func.sum(SaleItem.quantity * SaleItem.unit_price), 0))
            .join(Product, Product.brand_id == Brand.id)
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale)
            .where(Sale.status == SaleStatus.finalized)
            .group_by(Brand.name)
        )
        return [GroupReport(name=row[0], total=row[1]) for row in result.all()]

    async def top_products(self, limit: int = 5):
        result = await self.session.execute(
            select(Product.id, Product.name, func.coalesce(func.sum(SaleItem.quantity), 0))
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale)
            .where(Sale.status == SaleStatus.finalized)
            .group_by(Product.id, Product.name)
            .order_by(func.sum(SaleItem.quantity).desc())
            .limit(limit)
        )
        return [TopProductReport(product_id=str(row[0]), name=row[1], total=row[2]) for row in result.all()]

    async def stock_alerts(self, threshold: float):
        result = await self.session.execute(
            select(Product.id, Product.name, func.coalesce(func.sum(SaleItem.quantity), 0)).join(SaleItem, SaleItem.product_id == Product.id)
        )
        return [TopProductReport(product_id=str(row[0]), name=row[1], total=row[2]) for row in result.all() if row[2] <= threshold]
