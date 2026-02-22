from decimal import Decimal

from pydantic import BaseModel, Field


class PublicCatalogProductOut(BaseModel):
    id: str
    name: str
    sku: str | None = None
    image_url: str | None = None
    unit: str
    sell_price: Decimal
    category: str
    brand: str
    line: str | None = None
    on_hand: float
    variant_group: str | None = None
    variant_name: str | None = None


class PublicCatalogResponse(BaseModel):
    items: list[PublicCatalogProductOut]


class PublicCatalogOrderItemIn(BaseModel):
    product_id: str
    qty: float = Field(gt=0)


class PublicCatalogOrderCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=5, max_length=40)
    comment: str | None = Field(default=None, max_length=500)
    items: list[PublicCatalogOrderItemIn] = Field(min_length=1)


class PublicCatalogOrderOut(BaseModel):
    id: str
    status: str
