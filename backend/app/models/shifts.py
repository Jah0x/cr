import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class CashierShiftStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class CashierShift(Base):
    __tablename__ = "cashier_shifts"
    __table_args__ = (
        Index("ix_cashier_shifts_cashier_id_status", "cashier_id", "status"),
        Index("ix_cashier_shifts_store_id_opened_at", "store_id", "opened_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False)
    cashier_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    opened_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(CashierShiftStatus), nullable=False, default=CashierShiftStatus.open)
    opening_cash = Column(Numeric(12, 2), nullable=False, server_default="0")
    closing_cash = Column(Numeric(12, 2), nullable=True)
    note = Column(String, nullable=True)

    sales = relationship("Sale", back_populates="shift")
