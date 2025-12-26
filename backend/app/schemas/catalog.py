import uuid
from typing import Optional
from pydantic import BaseModel
from decimal import Decimal


class CategoryBase(BaseModel):
    name: str
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryOut(CategoryBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}


class BrandBase(BaseModel):
    name: str
    is_active: bool = True


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


class BrandOut(BrandBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}


class ProductLineBase(BaseModel):
    name: str
    brand_id: uuid.UUID
    is_active: bool = True


class ProductLineCreate(ProductLineBase):
    pass


class ProductLineUpdate(BaseModel):
    name: Optional[str] = None
    brand_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class ProductLineOut(ProductLineBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    sku: str
    name: str
    description: str = ""
    image_url: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    brand_id: Optional[uuid.UUID] = None
    line_id: Optional[uuid.UUID] = None
    price: Decimal
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    brand_id: Optional[uuid.UUID] = None
    line_id: Optional[uuid.UUID] = None
    price: Optional[Decimal] = None
    is_active: Optional[bool] = None


class ProductOut(ProductBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}
