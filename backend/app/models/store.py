import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class Store(Base):
    __tablename__ = "stores"
    __table_args__ = (Index("ix_stores_name", "name", unique=True),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    is_default = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    sales = relationship("Sale", back_populates="store")
    expenses = relationship("Expense", back_populates="store")
    stock_moves = relationship("StockMove", back_populates="store")
