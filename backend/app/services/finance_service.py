import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal
import uuid

from fastapi import HTTPException, status

from app.models.finance import (
    Expense,
    RecurringExpense,
    RecurringExpenseAllocationMethod,
    RecurringExpensePeriod,
)
from app.repos.finance_repo import (
    ExpenseAccrualRepo,
    ExpenseCategoryRepo,
    ExpenseRepo,
    RecurringExpenseRepo,
)
from app.repos.store_repo import StoreRepo


class AccrualService:
    def __init__(self, recurring_repo: RecurringExpenseRepo, accrual_repo: ExpenseAccrualRepo):
        self.recurring_repo = recurring_repo
        self.accrual_repo = accrual_repo

    async def ensure_accruals(self, store_id: uuid.UUID, date_from: date, date_to: date) -> None:
        recurring_expenses = await self.recurring_repo.list_for_accruals(
            store_id, date_from, date_to
        )
        for recurring_expense in recurring_expenses:
            active_from = max(date_from, recurring_expense.start_date)
            active_to = min(date_to, recurring_expense.end_date or date_to)
            if active_from > active_to:
                continue
            existing_dates = await self.accrual_repo.list_existing_dates(
                recurring_expense.id, active_from, active_to
            )
            payloads: list[dict] = []
            current = active_from
            while current <= active_to:
                if current not in existing_dates:
                    payloads.append(
                        {
                            "store_id": store_id,
                            "recurring_expense_id": recurring_expense.id,
                            "date": current,
                            "amount": self._daily_amount(recurring_expense, current),
                        }
                    )
                current += timedelta(days=1)
            await self.accrual_repo.bulk_create(payloads)

    def _daily_amount(self, recurring_expense: RecurringExpense, day: date) -> Decimal:
        amount = Decimal(recurring_expense.amount)
        if recurring_expense.period == RecurringExpensePeriod.daily:
            return amount
        if recurring_expense.period == RecurringExpensePeriod.weekly:
            return amount / Decimal("7")
        if recurring_expense.allocation_method == RecurringExpenseAllocationMethod.fixed_30:
            return amount / Decimal("30")
        days_in_month = Decimal(str(calendar.monthrange(day.year, day.month)[1]))
        return amount / days_in_month


class FinanceService:
    def __init__(
        self,
        category_repo: ExpenseCategoryRepo,
        expense_repo: ExpenseRepo,
        recurring_repo: RecurringExpenseRepo,
        accrual_service: AccrualService,
        store_repo: StoreRepo,
    ):
        self.category_repo = category_repo
        self.expense_repo = expense_repo
        self.recurring_repo = recurring_repo
        self.accrual_service = accrual_service
        self.store_repo = store_repo

    async def list_categories(self):
        return await self.category_repo.list()

    async def create_category(self, data: dict):
        return await self.category_repo.create(data)

    async def list_expenses(
        self,
        store_id: uuid.UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ):
        return await self.expense_repo.list(store_id, date_from, date_to)

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

    async def list_recurring_expenses(self, store_id: uuid.UUID | None = None):
        return await self.recurring_repo.list(store_id)

    async def create_recurring_expense(self, data: dict):
        payload = data.copy()
        if not payload.get("store_id"):
            payload["store_id"] = (await self.store_repo.get_default()).id
        return await self.recurring_repo.create(payload)

    async def update_recurring_expense(self, recurring_expense_id: uuid.UUID, data: dict):
        recurring_expense = await self.recurring_repo.get(recurring_expense_id)
        if not recurring_expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Recurring expense not found"
            )
        payload = data.copy()
        if payload.get("store_id") is None:
            payload.pop("store_id", None)
        return await self.recurring_repo.update(recurring_expense, payload)

    async def delete_recurring_expense(self, recurring_expense_id: uuid.UUID):
        recurring_expense = await self.recurring_repo.get(recurring_expense_id)
        if not recurring_expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Recurring expense not found"
            )
        return await self.recurring_repo.update(recurring_expense, {"is_active": False})

    async def ensure_accruals(self, store_id: uuid.UUID, date_from: date, date_to: date) -> None:
        await self.accrual_service.ensure_accruals(store_id, date_from, date_to)
