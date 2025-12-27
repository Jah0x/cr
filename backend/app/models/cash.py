import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class CashReceipt(Base):
    __tablename__ = "cash_receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    receipt_id = Column(String, nullable=False, unique=True)
    provider = Column(String, nullable=False)
    payload_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    sale = relationship("Sale", back_populates="receipts")


class CashRegister(Base):
    __tablename__ = "cash_registers"
    __table_args__ = (Index("ix_cash_registers_active", "is_active"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)
    config = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, server_default="true")
