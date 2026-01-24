import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Enum, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class TenantStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    provisioning_failed = "provisioning_failed"


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = (Index("ix_tenants_status", "status"), {"schema": "public"})

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    status = Column(Enum(TenantStatus), nullable=False, default=TenantStatus.active)
    last_error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
