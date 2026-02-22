import uuid
from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal

from app.models.catalog import ProductUnit


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
    sku: Optional[str] = None
    barcode: Optional[str] = None
    name: str
    description: str = ""
    image_url: Optional[str] = None
    category_id: uuid.UUID
    brand_id: uuid.UUID
    line_id: Optional[uuid.UUID] = None
    unit: ProductUnit = ProductUnit.pcs
    purchase_price: Decimal = Field(default=0, ge=0)
    cost_price: Decimal = Field(default=0, ge=0)
    sell_price: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(ge=0)
    is_active: bool = True
    is_hidden: bool = False
    variant_group: Optional[str] = None
    variant_name: Optional[str] = None


class ProductCreate(ProductBase):
    name: Optional[str] = None


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    barcode: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    brand_id: Optional[uuid.UUID] = None
    line_id: Optional[uuid.UUID] = None
    unit: Optional[ProductUnit] = None
    purchase_price: Optional[Decimal] = Field(default=None, ge=0)
    cost_price: Optional[Decimal] = Field(default=None, ge=0)
    sell_price: Optional[Decimal] = Field(default=None, ge=0)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    is_hidden: Optional[bool] = None
    variant_group: Optional[str] = None
    variant_name: Optional[str] = None


class ProductOut(ProductBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}
