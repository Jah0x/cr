import uuid
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel

from app.models.sales import SaleStatus


class SaleItemIn(BaseModel):
    product_id: uuid.UUID
    qty: Decimal
    unit_price: Decimal | None = None


class SaleCreate(BaseModel):
    items: list[SaleItemIn]
    currency: str | None = None


class SaleItemOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID | None
    qty: Decimal
    unit_price: Decimal
    line_total: Decimal

    model_config = {"from_attributes": True}


class CashReceiptOut(BaseModel):
    id: uuid.UUID
    receipt_id: str
    provider: str

    model_config = {"from_attributes": True}


class SaleOut(BaseModel):
    id: uuid.UUID
    status: SaleStatus
    total_amount: Decimal
    currency: str | None
    created_at: datetime
    created_by_user_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class SaleDetail(SaleOut):
    items: list[SaleItemOut]
    receipts: list[CashReceiptOut]
