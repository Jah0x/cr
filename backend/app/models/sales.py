import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, ForeignKey, Enum, DateTime, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class SaleStatus(str, enum.Enum):
    draft = "draft"
    completed = "completed"
    cancelled = "cancelled"


class PaymentProvider(str, enum.Enum):
    cash = "cash"
    card = "card"
    transfer = "transfer"

    @classmethod
    def _missing_(cls, value):
        if value == "external":
            return cls.transfer
        return None

    @classmethod
    def normalize(cls, value: object) -> str | None:
        if isinstance(value, cls):
            return value.value
        if value == "external":
            return cls.transfer.value
        if isinstance(value, str):
            return value
        return None


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (Index("ix_sales_status", "status"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    status = Column(Enum(SaleStatus), default=SaleStatus.draft, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False, server_default="0")
    currency = Column(String, default="")
    send_to_terminal = Column(Boolean, nullable=False, server_default="false")

    items = relationship("SaleItem", back_populates="sale")
    tax_lines = relationship("SaleTaxLine", back_populates="sale")
    receipts = relationship("CashReceipt", back_populates="sale")
    payments = relationship("Payment", back_populates="sale")
    refunds = relationship("Refund", back_populates="sale")


class SaleItem(Base):
    __tablename__ = "sale_items"
    __table_args__ = (
        Index("ix_sale_items_sale_id", "sale_id"),
        Index("ix_sale_items_product_id", "product_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"))
    qty = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)
    cost_snapshot = Column(Numeric(12, 2), nullable=False, default=0)
    profit_line = Column(Numeric(12, 2), nullable=False, default=0)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")
    allocations = relationship("SaleItemCostAllocation", back_populates="sale_item")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (Index("ix_payments_status", "status"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, default="")
    method = Column(Enum(PaymentProvider), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.pending)
    reference = Column(String, default="")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    sale = relationship("Sale", back_populates="payments")


class SaleTaxLine(Base):
    __tablename__ = "sale_tax_lines"
    __table_args__ = (
        Index("ix_sale_tax_lines_sale_id", "sale_id"),
        Index("ix_sale_tax_lines_rule_id", "rule_id"),
        Index("ix_sale_tax_lines_method", "method"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(String, nullable=False)
    rule_name = Column(String, nullable=False)
    rate = Column(Numeric(5, 2), nullable=False)
    method = Column(Enum(PaymentProvider), nullable=True)
    taxable_amount = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    sale = relationship("Sale", back_populates="tax_lines")


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(String, default="")
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    sale = relationship("Sale", back_populates="refunds")
