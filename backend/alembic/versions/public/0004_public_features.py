"""Add public features and remove tenant-scoped tables.

Revision ID: 0004_public_features
Revises: 0003_public_tenant_ui_prefs
Create Date: 2025-09-27 00:20:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "features",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("code", name="uq_features_code"),
        schema="public",
    )
    op.drop_table("tenant_ui_prefs", schema="public")
    op.drop_index("ix_tenant_features_tenant_id", table_name="tenant_features", schema="public")
    op.drop_table("tenant_features", schema="public")
    op.drop_index("ix_tenant_modules_tenant_id", table_name="tenant_modules", schema="public")
    op.drop_table("tenant_modules", schema="public")


def downgrade() -> None:
    op.create_table(
        "tenant_modules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("module_id", UUID(as_uuid=True), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["public.modules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["public.tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "module_id", name="uq_tenant_modules_tenant_module"),
        schema="public",
    )
    op.create_index("ix_tenant_modules_tenant_id", "tenant_modules", ["tenant_id"], schema="public")
    op.create_table(
        "tenant_features",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["public.tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_tenant_features_tenant_code"),
        schema="public",
    )
    op.create_index("ix_tenant_features_tenant_id", "tenant_features", ["tenant_id"], schema="public")
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
    op.drop_table("features", schema="public")
