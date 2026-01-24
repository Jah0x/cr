"""Add tenant domains and provisioning status.

Revision ID: public_0009
Revises: public_0008
Create Date: 2025-10-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "public_0009"
down_revision = "public_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE public.tenantstatus ADD VALUE IF NOT EXISTS 'provisioning_failed'")
    op.add_column("tenants", sa.Column("last_error", sa.String(), nullable=True), schema="public")

    op.add_column(
        "tenant_invitations",
        sa.Column("role_name", sa.String(), nullable=False, server_default="owner"),
        schema="public",
    )
    op.add_column(
        "tenant_invitations",
        sa.Column("token", sa.String(), nullable=True),
        schema="public",
    )

    op.create_table(
        "tenant_domains",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["public.tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("domain", name="uq_tenant_domains_domain"),
        schema="public",
    )
    op.create_index("ix_tenant_domains_tenant_id", "tenant_domains", ["tenant_id"], schema="public")


def downgrade() -> None:
    op.drop_index("ix_tenant_domains_tenant_id", table_name="tenant_domains", schema="public")
    op.drop_table("tenant_domains", schema="public")

    op.drop_column("tenant_invitations", "token", schema="public")
    op.drop_column("tenant_invitations", "role_name", schema="public")

    op.drop_column("tenants", "last_error", schema="public")
