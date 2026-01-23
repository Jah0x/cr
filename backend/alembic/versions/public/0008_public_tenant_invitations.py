"""Add tenant invitations.

Revision ID: public_0009
Revises: public_0008
Create Date: 2025-10-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "public_0009"
down_revision = "public_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_invitations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["public.tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash", name="uq_tenant_invitations_token_hash"),
        schema="public",
    )
    op.create_index(
        "ix_tenant_invitations_tenant_id",
        "tenant_invitations",
        ["tenant_id"],
        unique=False,
        schema="public",
    )
    op.create_index(
        "ix_tenant_invitations_email",
        "tenant_invitations",
        ["email"],
        unique=False,
        schema="public",
    )


def downgrade() -> None:
    op.drop_index("ix_tenant_invitations_email", table_name="tenant_invitations", schema="public")
    op.drop_index("ix_tenant_invitations_tenant_id", table_name="tenant_invitations", schema="public")
    op.drop_table("tenant_invitations", schema="public")
