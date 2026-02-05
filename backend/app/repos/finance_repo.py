from datetime import date, datetime
from typing import List
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Expense, ExpenseAccrual, ExpenseCategory, RecurringExpense


class ExpenseCategoryRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> List[ExpenseCategory]:
        result = await self.session.execute(select(ExpenseCategory).order_by(ExpenseCategory.name))
        return result.scalars().all()

    async def create(self, data: dict) -> ExpenseCategory:
        category = ExpenseCategory(**data)
        self.session.add(category)
        await self.session.flush()
        return category


class ExpenseRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        store_id: uuid.UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> List[Expense]:
        stmt = select(Expense).order_by(Expense.occurred_at.desc())
        if store_id:
            stmt = stmt.where(Expense.store_id == store_id)
        if date_from:
            stmt = stmt.where(Expense.occurred_at >= date_from)
        if date_to:
            stmt = stmt.where(Expense.occurred_at <= date_to)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: dict) -> Expense:
        expense = Expense(**data)
        self.session.add(expense)
        await self.session.flush()
        return expense

    async def delete(self, expense: Expense) -> None:
        await self.session.delete(expense)


class RecurringExpenseRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, store_id: uuid.UUID | None = None) -> List[RecurringExpense]:
        stmt = select(RecurringExpense).order_by(RecurringExpense.created_at.desc())
        if store_id:
            stmt = stmt.where(RecurringExpense.store_id == store_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: dict) -> RecurringExpense:
        recurring_expense = RecurringExpense(**data)
        self.session.add(recurring_expense)
        await self.session.flush()
        return recurring_expense

    async def get(self, recurring_expense_id: uuid.UUID) -> RecurringExpense | None:
        return await self.session.get(RecurringExpense, recurring_expense_id)

    async def update(self, recurring_expense: RecurringExpense, data: dict) -> RecurringExpense:
        for key, value in data.items():
            setattr(recurring_expense, key, value)
        await self.session.flush()
        return recurring_expense

    async def list_for_accruals(
        self, store_id: uuid.UUID, date_from: date, date_to: date
    ) -> List[RecurringExpense]:
        stmt = (
            select(RecurringExpense)
            .where(
                RecurringExpense.store_id == store_id,
                RecurringExpense.is_active.is_(True),
                RecurringExpense.start_date <= date_to,
                (RecurringExpense.end_date.is_(None)) | (RecurringExpense.end_date >= date_from),
            )
            .order_by(RecurringExpense.start_date.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ExpenseAccrualRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_existing_dates(
        self, recurring_expense_id: uuid.UUID, date_from: date, date_to: date
    ) -> set[date]:
        stmt = select(ExpenseAccrual.date).where(
            ExpenseAccrual.recurring_expense_id == recurring_expense_id,
            ExpenseAccrual.date >= date_from,
            ExpenseAccrual.date <= date_to,
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())

    async def bulk_create(self, payloads: list[dict]) -> None:
        if not payloads:
            return
        self.session.add_all([ExpenseAccrual(**payload) for payload in payloads])
        await self.session.flush()
