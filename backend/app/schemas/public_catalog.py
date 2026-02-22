from decimal import Decimal

from pydantic import BaseModel


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


class PublicCatalogResponse(BaseModel):
    items: list[PublicCatalogProductOut]
