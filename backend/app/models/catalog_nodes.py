import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


class CatalogNode(Base):
    __tablename__ = "catalog_nodes"
    __table_args__ = (
        Index("ix_catalog_nodes_parent_level", "parent_id", "level_code"),
        Index("uq_catalog_nodes_parent_level_name", "parent_id", "level_code", text("lower(name)"), unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level_code = Column(String, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("catalog_nodes.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=True)
    meta = Column(JSONB, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    parent = relationship("CatalogNode", remote_side=[id], backref="children")
