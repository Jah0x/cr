import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class TenantDomain(Base):
    __tablename__ = "tenant_domains"
    __table_args__ = (
        Index("ix_tenant_domains_tenant_id", "tenant_id"),
        Index("ix_tenant_domains_domain", "domain", unique=True),
        {"schema": "public"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False)
    domain = Column(String, nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
