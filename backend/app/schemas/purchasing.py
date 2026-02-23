import uuid
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field

from app.models.purchasing import PurchaseStatus


class SupplierBase(BaseModel):
    name: str
    contact: str = ""


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None


class SupplierOut(SupplierBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}


class PurchaseItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: Decimal
    unit_cost: Decimal


class PurchaseItemOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal
    unit_cost: Decimal

    model_config = {"from_attributes": True}


class PurchaseInvoiceCreate(BaseModel):
    supplier_id: Optional[uuid.UUID] = None


class PurchaseInvoiceOut(BaseModel):
    id: uuid.UUID
    supplier_id: Optional[uuid.UUID]
    status: PurchaseStatus

    model_config = {"from_attributes": True}


class PurchaseInvoiceDetail(PurchaseInvoiceOut):
    items: List[PurchaseItemOut] = Field(default_factory=list)


class PurchasePostResult(BaseModel):
    id: uuid.UUID
    status: PurchaseStatus
