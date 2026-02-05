import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel

from app.models.sales import PaymentProvider, PaymentStatus, SaleStatus


class SaleItemIn(BaseModel):
    product_id: uuid.UUID
    qty: Decimal
    unit_price: Decimal | None = None


class PaymentIn(BaseModel):
    amount: Decimal
    method: PaymentProvider
    currency: str | None = None
    status: PaymentStatus | None = None
    reference: str | None = None


class SaleCreate(BaseModel):
    store_id: uuid.UUID | None = None
    items: list[SaleItemIn]
    currency: str | None = None
    payments: list[PaymentIn] | None = None
    cash_register_id: uuid.UUID | None = None
    send_to_terminal: bool = False


class SaleDraftCreate(BaseModel):
    store_id: uuid.UUID | None = None
    currency: str | None = None
    send_to_terminal: bool = False


class SaleDraftUpdate(BaseModel):
    store_id: uuid.UUID | None = None
    items: list[SaleItemIn]
    currency: str | None = None
    send_to_terminal: bool | None = None


class SaleComplete(BaseModel):
    payments: list[PaymentIn] | None = None
    cash_register_id: uuid.UUID | None = None


class SaleItemOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID | None
    qty: Decimal
    unit_price: Decimal
    line_total: Decimal
    cost_snapshot: Decimal
    profit_line: Decimal

    model_config = {"from_attributes": True}


class CashReceiptOut(BaseModel):
    id: uuid.UUID
    receipt_id: str
    provider: str

    model_config = {"from_attributes": True}


class PaymentOut(BaseModel):
    id: uuid.UUID
    amount: Decimal
    currency: str
    method: PaymentProvider
    status: PaymentStatus
    reference: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RefundOut(BaseModel):
    id: uuid.UUID
    amount: Decimal
    reason: str | None
    created_by_user_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SaleOut(BaseModel):
    id: uuid.UUID
    status: SaleStatus
    total_amount: Decimal
    currency: str | None
    created_at: datetime
    created_by_user_id: uuid.UUID | None
    send_to_terminal: bool
    store_id: uuid.UUID
    payments: list[PaymentOut] = []

    model_config = {"from_attributes": True}


class SaleDetail(SaleOut):
    items: list[SaleItemOut]
    receipts: list[CashReceiptOut]
    refunds: list[RefundOut]


class RefundItemIn(BaseModel):
    sale_item_id: uuid.UUID
    qty: Decimal


class RefundCreate(BaseModel):
    amount: Decimal | None = None
    reason: str | None = None
    items: list[RefundItemIn] | None = None
