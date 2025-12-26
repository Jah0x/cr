import uuid
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel

from app.models.sales import SaleStatus, PaymentProvider


class SaleCreate(BaseModel):
    customer_name: str = ""


class SaleOut(BaseModel):
    id: uuid.UUID
    status: SaleStatus
    customer_name: str

    model_config = {"from_attributes": True}


class SaleItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal = 0


class SaleItemUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None


class SaleItemOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal

    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    amount: Decimal
    provider: PaymentProvider
    reference: str = ""


class PaymentOut(BaseModel):
    id: uuid.UUID
    amount: Decimal
    provider: PaymentProvider
    reference: str

    model_config = {"from_attributes": True}


class SaleDetail(SaleOut):
    items: List[SaleItemOut] = []
    payments: List[PaymentOut] = []
