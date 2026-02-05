import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class StockMove(Base):
    __tablename__ = "stock_moves"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    delta_qty = Column(Numeric(12, 3), nullable=False, server_default="0")
    reason = Column(String, nullable=False)
    reference = Column(String, default="")
    ref_id = Column(UUID(as_uuid=True))
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="RESTRICT"), nullable=True)

    product = relationship("Product")
    store = relationship("Store", back_populates="stock_moves")


class StockBatch(Base):
    __tablename__ = "stock_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    purchase_item_id = Column(UUID(as_uuid=True), ForeignKey("purchase_items.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    product = relationship("Product")
    purchase_item = relationship("PurchaseItem")
    allocations = relationship("SaleItemCostAllocation", back_populates="batch")


class SaleItemCostAllocation(Base):
    __tablename__ = "sale_item_cost_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_item_id = Column(UUID(as_uuid=True), ForeignKey("sale_items.id", ondelete="CASCADE"), nullable=False)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("stock_batches.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)

    batch = relationship("StockBatch", back_populates="allocations")
    sale_item = relationship("SaleItem", back_populates="allocations")
