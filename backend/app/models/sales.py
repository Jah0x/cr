import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, ForeignKey, Enum, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class SaleStatus(str, enum.Enum):
    completed = "completed"
    void = "void"


class PaymentProvider(str, enum.Enum):
    cash = "cash"
    card = "card"
    external = "external"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (Index("ix_sales_status", "status"), Index("ix_sales_tenant_id", "tenant_id"))

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    status = Column(Enum(SaleStatus), default=SaleStatus.completed, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False, server_default="0")
    currency = Column(String, default="")
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)

    items = relationship("SaleItem", back_populates="sale")
    receipts = relationship("CashReceipt", back_populates="sale")
    payments = relationship("Payment", back_populates="sale")
    refunds = relationship("Refund", back_populates="sale")


class SaleItem(Base):
    __tablename__ = "sale_items"
    __table_args__ = (
        Index("ix_sale_items_sale_id", "sale_id"),
        Index("ix_sale_items_product_id", "product_id"),
        Index("ix_sale_items_tenant_id", "tenant_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"))
    qty = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")
    allocations = relationship("SaleItemCostAllocation", back_populates="sale_item")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (Index("ix_payments_status", "status"), Index("ix_payments_tenant_id", "tenant_id"))

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="")
    method = Column(Enum(PaymentProvider), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.pending)
    reference = Column(String, default="")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)

    sale = relationship("Sale", back_populates="payments")


class Refund(Base):
    __tablename__ = "refunds"
    __table_args__ = (Index("ix_refunds_tenant_id", "tenant_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(String, default="")
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)

    sale = relationship("Sale", back_populates="refunds")
