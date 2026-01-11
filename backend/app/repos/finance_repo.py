from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Expense, ExpenseCategory


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

    async def list(self, date_from: datetime | None = None, date_to: datetime | None = None) -> List[Expense]:
        stmt = select(Expense).order_by(Expense.occurred_at.desc())
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
