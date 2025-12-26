import uuid
from typing import Optional
from pydantic import BaseModel
from decimal import Decimal


class CategoryBase(BaseModel):
    name: str
    active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None


class CategoryOut(CategoryBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}


class BrandBase(BaseModel):
    name: str
    active: bool = True


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None


class BrandOut(BrandBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}


class ProductLineBase(BaseModel):
    name: str
    brand_id: uuid.UUID
    active: bool = True


class ProductLineCreate(ProductLineBase):
    pass


class ProductLineUpdate(BaseModel):
    name: Optional[str] = None
    brand_id: Optional[uuid.UUID] = None
    active: Optional[bool] = None


class ProductLineOut(ProductLineBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    sku: str
    name: str
    description: str = ""
    category_id: Optional[uuid.UUID] = None
    brand_id: Optional[uuid.UUID] = None
    line_id: Optional[uuid.UUID] = None
    price: Decimal
    active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    brand_id: Optional[uuid.UUID] = None
    line_id: Optional[uuid.UUID] = None
    price: Optional[Decimal] = None
    active: Optional[bool] = None


class ProductOut(ProductBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}
