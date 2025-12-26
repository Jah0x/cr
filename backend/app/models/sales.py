import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class SaleStatus(str, enum.Enum):
    draft = "draft"
    finalized = "finalized"
    void = "void"


class PaymentProvider(str, enum.Enum):
    cash = "cash"
    card = "card"
    external = "external"


class Sale(Base):
    __tablename__ = "sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(Enum(SaleStatus), default=SaleStatus.draft, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    customer_name = Column(String, default="")

    items = relationship("SaleItem", back_populates="sale")
    payments = relationship("Payment", back_populates="sale")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"))
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")
    allocations = relationship("SaleItemCostAllocation", back_populates="sale_item")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    provider = Column(Enum(PaymentProvider), nullable=False)
    reference = Column(String, default="")

    sale = relationship("Sale", back_populates="payments")
