"""Tenant settings tables.

Revision ID: 0002_tenant_settings
Revises: 0001_tenant_base
Create Date: 2025-09-27 00:20:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0002_tenant_settings"
down_revision = "0001_tenant_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_modules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("module_id", UUID(as_uuid=True), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["public.modules.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("module_id", name="uq_tenant_modules_module_id"),
    )
    op.create_index("ix_tenant_modules_module_id", "tenant_modules", ["module_id"])
    op.create_table(
        "tenant_features",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("code", name="uq_tenant_features_code"),
    )
    op.create_index("ix_tenant_features_code", "tenant_features", ["code"])
    op.create_table(
        "tenant_ui_prefs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("prefs", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("tenant_ui_prefs")
    op.drop_index("ix_tenant_features_code", table_name="tenant_features")
    op.drop_table("tenant_features")
    op.drop_index("ix_tenant_modules_module_id", table_name="tenant_modules")
    op.drop_table("tenant_modules")
