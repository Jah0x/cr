from datetime import datetime
from decimal import Decimal
import uuid

from pydantic import BaseModel


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
