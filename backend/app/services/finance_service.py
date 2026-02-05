from datetime import datetime

from fastapi import HTTPException, status

from app.models.finance import Expense
from app.repos.finance_repo import ExpenseCategoryRepo, ExpenseRepo
from app.repos.store_repo import StoreRepo


class FinanceService:
    def __init__(self, category_repo: ExpenseCategoryRepo, expense_repo: ExpenseRepo, store_repo: StoreRepo):
        self.category_repo = category_repo
        self.expense_repo = expense_repo
        self.store_repo = store_repo

    async def list_categories(self):
        return await self.category_repo.list()

    async def create_category(self, data: dict):
        return await self.category_repo.create(data)

    async def list_expenses(self, date_from: datetime | None = None, date_to: datetime | None = None):
        return await self.expense_repo.list(date_from, date_to)

    async def create_expense(self, data: dict, user_id):
        payload = data.copy()
        payload["created_by_user_id"] = user_id
        if not payload.get("store_id"):
            payload["store_id"] = (await self.store_repo.get_default()).id
        return await self.expense_repo.create(payload)

    async def delete_expense(self, expense_id):
        expense = await self.expense_repo.session.get(Expense, expense_id)
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
        await self.expense_repo.delete(expense)
