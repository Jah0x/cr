from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
import uuid

from pydantic import BaseModel, field_serializer

from app.models.finance import RecurringExpenseAllocationMethod, RecurringExpensePeriod


class ExpenseCategoryCreate(BaseModel):
    name: str


class ExpenseCategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ExpenseCreate(BaseModel):
    store_id: uuid.UUID | None = None
    occurred_at: datetime
    amount: Decimal
    category_id: uuid.UUID | None = None
    note: str | None = None
    payment_method: str | None = None


class ExpenseOut(BaseModel):
    id: uuid.UUID
    occurred_at: datetime
    amount: Decimal
    category_id: uuid.UUID | None
    note: str | None
    payment_method: str | None
    created_by_user_id: uuid.UUID | None
    created_at: datetime
    store_id: uuid.UUID

    model_config = {"from_attributes": True}


class RecurringExpenseCreate(BaseModel):
    store_id: uuid.UUID | None = None
    name: str
    amount: Decimal
    period: RecurringExpensePeriod
    allocation_method: RecurringExpenseAllocationMethod = (
        RecurringExpenseAllocationMethod.calendar_days
    )
    start_date: date
    end_date: date | None = None
    is_active: bool = True


class RecurringExpenseUpdate(BaseModel):
    store_id: uuid.UUID | None = None
    name: str
    amount: Decimal
    period: RecurringExpensePeriod
    allocation_method: RecurringExpenseAllocationMethod
    start_date: date
    end_date: date | None = None
    is_active: bool


class RecurringExpenseOut(BaseModel):
    id: uuid.UUID
    store_id: uuid.UUID
    name: str
    amount: Decimal
    period: RecurringExpensePeriod
    allocation_method: RecurringExpenseAllocationMethod
    start_date: date
    end_date: date | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FinanceDecimalModel(BaseModel):
    @field_serializer("*", when_used="json")
    def serialize_decimals(self, value):
        if isinstance(value, Decimal):
            return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return value


class ProfitLossDailyBreakdown(FinanceDecimalModel):
    date: date
    revenue: Decimal
    cogs: Decimal
    taxes: Decimal
    one_time_expenses: Decimal
    fixed_costs: Decimal
    operating_profit: Decimal


class ProfitLossTotals(FinanceDecimalModel):
    revenue_total: Decimal
    cogs_total: Decimal
    taxes_total: Decimal
    one_time_expenses_total: Decimal
    fixed_accruals_total: Decimal
    gross_profit: Decimal
    operating_profit: Decimal
    profitable: bool


class ProfitLossResponse(FinanceDecimalModel):
    totals: ProfitLossTotals
    daily_breakdown: list[ProfitLossDailyBreakdown]
