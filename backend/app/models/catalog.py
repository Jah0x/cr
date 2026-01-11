import uuid
from sqlalchemy import Column, String, Boolean, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        Index("ix_categories_name", "name", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    products = relationship("Product", back_populates="category")


class Brand(Base):
    __tablename__ = "brands"
    __table_args__ = (
        Index("ix_brands_name", "name", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    lines = relationship("ProductLine", back_populates="brand")


class ProductLine(Base):
    __tablename__ = "product_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True)

    brand = relationship("Brand", back_populates="lines")
    products = relationship("Product", back_populates="line")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_sku", "sku", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    image_url = Column(String, nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"))
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"))
    line_id = Column(UUID(as_uuid=True), ForeignKey("product_lines.id", ondelete="SET NULL"))
    price = Column(Numeric(12, 2), nullable=False, default=0)
    last_purchase_unit_cost = Column(Numeric(12, 2), nullable=False, default=0)
    is_active = Column(Boolean, default=True)

    category = relationship("Category", back_populates="products")
    brand = relationship("Brand")
    line = relationship("ProductLine", back_populates="products")
    purchase_items = relationship("PurchaseItem", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")
