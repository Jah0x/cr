from datetime import date, datetime
from decimal import Decimal
import uuid

from pydantic import BaseModel

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
