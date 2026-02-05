import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class StockAdjustmentCreate(BaseModel):
    store_id: uuid.UUID | None = None
    product_id: uuid.UUID
    quantity: Decimal
    reason: str


class StockMoveOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal
    delta_qty: Decimal
    reason: str
    reference: str
    created_at: datetime
    store_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class StockQuery(BaseModel):
    product_id: uuid.UUID
    on_hand: Decimal
