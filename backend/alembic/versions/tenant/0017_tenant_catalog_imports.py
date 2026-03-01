"""Add catalog imports table.

Revision ID: tenant_0017
Revises: tenant_0016
Create Date: 2026-03-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "tenant_0017"
down_revision = "tenant_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_imports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_code", sa.Text(), nullable=False),
        sa.Column("filename", sa.Text(), nullable=True),
        sa.Column("uploaded_by", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "error_log",
            JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_catalog_imports_tenant_code",
        "catalog_imports",
        ["tenant_code"],
        unique=False,
    )
    op.create_index(
        "ix_catalog_imports_created_at",
        "catalog_imports",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_catalog_imports_created_at", table_name="catalog_imports")
    op.drop_index("ix_catalog_imports_tenant_code", table_name="catalog_imports")
    op.drop_table("catalog_imports")
