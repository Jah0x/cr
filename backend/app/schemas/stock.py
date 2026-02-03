import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class StockAdjustmentCreate(BaseModel):
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

    model_config = {"from_attributes": True}


class StockQuery(BaseModel):
    product_id: uuid.UUID
    on_hand: Decimal
