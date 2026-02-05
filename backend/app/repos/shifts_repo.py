from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sales import Payment, Sale, SaleItem, SaleTaxLine, SaleStatus
from app.models.shifts import CashierShift, CashierShiftStatus


class CashierShiftRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> CashierShift:
        shift = CashierShift(**data)
        self.session.add(shift)
        await self.session.flush()
        return shift

    async def get(self, shift_id) -> CashierShift | None:
        result = await self.session.execute(
            select(CashierShift)
            .where(CashierShift.id == shift_id)
            .options(selectinload(CashierShift.sales).selectinload(Sale.payments), selectinload(CashierShift.sales).selectinload(Sale.items))
        )
        return result.scalar_one_or_none()

    async def get_active_for_cashier(self, cashier_id) -> CashierShift | None:
        result = await self.session.execute(
            select(CashierShift)
            .where(CashierShift.cashier_id == cashier_id, CashierShift.status == CashierShiftStatus.open)
            .order_by(CashierShift.opened_at.desc())
        )
        return result.scalar_one_or_none()

    async def get_active_for_cashier_store(self, cashier_id, store_id) -> CashierShift | None:
        result = await self.session.execute(
            select(CashierShift)
            .where(
                CashierShift.cashier_id == cashier_id,
                CashierShift.store_id == store_id,
                CashierShift.status == CashierShiftStatus.open,
            )
            .order_by(CashierShift.opened_at.desc())
        )
        return result.scalar_one_or_none()

    async def list(self, store_id=None, date_from=None, date_to=None, cashier_id=None, status=None) -> list[CashierShift]:
        stmt = select(CashierShift)
        if store_id:
            stmt = stmt.where(CashierShift.store_id == store_id)
        if date_from:
            stmt = stmt.where(CashierShift.opened_at >= date_from)
        if date_to:
            stmt = stmt.where(CashierShift.opened_at <= date_to)
        if cashier_id:
            stmt = stmt.where(CashierShift.cashier_id == cashier_id)
        if status:
            stmt = stmt.where(CashierShift.status == status)
        stmt = stmt.order_by(CashierShift.opened_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_sales(self, shift_id):
        result = await self.session.execute(
            select(Sale)
            .where(Sale.shift_id == shift_id)
            .options(selectinload(Sale.payments), selectinload(Sale.items), selectinload(Sale.tax_lines))
            .order_by(Sale.created_at.desc())
        )
        return result.scalars().all()

    async def get_aggregates(self, shift_id) -> dict:
        sales_count_result = await self.session.execute(
            select(func.count(Sale.id), func.coalesce(func.sum(Sale.total_amount), 0))
            .where(Sale.shift_id == shift_id, Sale.status == SaleStatus.completed)
        )
        sales_count, revenue_total = sales_count_result.one()

        tax_result = await self.session.execute(
            select(func.coalesce(func.sum(SaleTaxLine.tax_amount), 0)).join(Sale, Sale.id == SaleTaxLine.sale_id).where(Sale.shift_id == shift_id)
        )
        tax_total = tax_result.scalar_one()

        profit_result = await self.session.execute(
            select(func.coalesce(func.sum(SaleItem.profit_line), 0)).join(Sale, Sale.id == SaleItem.sale_id).where(Sale.shift_id == shift_id, Sale.status == SaleStatus.completed)
        )
        profit_total = profit_result.scalar_one()

        payment_rows = await self.session.execute(
            select(Payment.method, func.coalesce(func.sum(Payment.amount), 0))
            .join(Sale, Sale.id == Payment.sale_id)
            .where(Sale.shift_id == shift_id)
            .group_by(Payment.method)
        )
        by_payment_type = {method: amount for method, amount in payment_rows.all()}

        return {
            "sales_count": sales_count or 0,
            "revenue_total": Decimal(revenue_total or 0),
            "tax_total": Decimal(tax_total or 0),
            "profit_gross_total": Decimal(profit_total or 0),
            "by_payment_type": by_payment_type,
        }
