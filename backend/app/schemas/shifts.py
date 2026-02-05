import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.sales import PaymentProvider
from app.models.shifts import CashierShiftStatus
from app.schemas.sales import SaleOut


class ShiftOpenIn(BaseModel):
    store_id: uuid.UUID
    opening_cash: Decimal = Decimal("0")
    note: str | None = None


class ShiftCloseIn(BaseModel):
    closing_cash: Decimal | None = None
    note: str | None = None


class ShiftOut(BaseModel):
    id: uuid.UUID
    store_id: uuid.UUID
    cashier_id: uuid.UUID
    opened_at: datetime
    closed_at: datetime | None
    status: CashierShiftStatus
    opening_cash: Decimal
    closing_cash: Decimal | None
    note: str | None

    model_config = {"from_attributes": True}


class ShiftListFilters(BaseModel):
    store_id: uuid.UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    cashier_id: uuid.UUID | None = None
    status: CashierShiftStatus | None = None


class ShiftAggregates(BaseModel):
    sales_count: int
    revenue_total: Decimal
    tax_total: Decimal
    profit_gross_total: Decimal
    by_payment_type: dict[PaymentProvider, Decimal]


class ShiftDetail(ShiftOut):
    aggregates: ShiftAggregates
    sales: list[SaleOut]
