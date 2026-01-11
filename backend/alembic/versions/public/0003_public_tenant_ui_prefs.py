"""Tenant UI preferences.

Revision ID: 0003_public_tenant_ui_prefs
Revises: 0002_public_platform
Create Date: 2025-09-27 00:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0003_public_tenant_ui_prefs"
down_revision = "0002_public_platform"
branch_labels = ("public",)
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_ui_prefs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("prefs", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["public.tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_ui_prefs_tenant"),
        schema="public",
    )


def downgrade() -> None:
    op.drop_table("tenant_ui_prefs", schema="public")
