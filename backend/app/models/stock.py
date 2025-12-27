import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class StockMove(Base):
    __tablename__ = "stock_moves"
    __table_args__ = (Index("ix_stock_moves_tenant_id", "tenant_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    delta_qty = Column(Numeric(12, 3), nullable=False, server_default="0")
    reason = Column(String, nullable=False)
    reference = Column(String, default="")
    ref_id = Column(UUID(as_uuid=True))
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)

    product = relationship("Product")


class StockBatch(Base):
    __tablename__ = "stock_batches"
    __table_args__ = (Index("ix_stock_batches_tenant_id", "tenant_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    purchase_item_id = Column(UUID(as_uuid=True), ForeignKey("purchase_items.id", ondelete="SET NULL"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)

    product = relationship("Product")
    purchase_item = relationship("PurchaseItem")
    allocations = relationship("SaleItemCostAllocation", back_populates="batch")


class SaleItemCostAllocation(Base):
    __tablename__ = "sale_item_cost_allocations"
    __table_args__ = (Index("ix_sale_item_cost_allocations_tenant_id", "tenant_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_item_id = Column(UUID(as_uuid=True), ForeignKey("sale_items.id", ondelete="CASCADE"), nullable=False)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("stock_batches.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)

    batch = relationship("StockBatch", back_populates="allocations")
    sale_item = relationship("SaleItem", back_populates="allocations")
