import uuid
from sqlalchemy import Column, String, Numeric, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.core.db import Base


class PurchaseStatus(str, enum.Enum):
    draft = "draft"
    posted = "posted"
    void = "void"


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    contact = Column(String, default="")

    invoices = relationship("PurchaseInvoice", back_populates="supplier")


class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="SET NULL"))
    status = Column(Enum(PurchaseStatus), default=PurchaseStatus.draft, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    supplier = relationship("Supplier", back_populates="invoices")
    items = relationship("PurchaseItem", back_populates="invoice")


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("purchase_invoices.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False)

    invoice = relationship("PurchaseInvoice", back_populates="items")
    product = relationship("Product", back_populates="purchase_items")
