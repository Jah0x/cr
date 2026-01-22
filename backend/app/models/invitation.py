import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class TenantInvitation(Base):
    __tablename__ = "tenant_invitations"
    __table_args__ = (
        Index("ix_tenant_invitations_token_hash", "token_hash", unique=True),
        Index("ix_tenant_invitations_tenant_id", "tenant_id"),
        Index("ix_tenant_invitations_email", "email"),
        {"schema": "public"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("public.tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String, nullable=False)
    token_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
