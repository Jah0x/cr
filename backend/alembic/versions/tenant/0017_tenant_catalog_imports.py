"""Add catalog imports table.

Revision ID: tenant_0017
Revises: tenant_0016
Create Date: 2026-03-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "tenant_0017"
down_revision = "tenant_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_imports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="queued"),
        sa.Column("mode", sa.String(), nullable=False, server_default="sync"),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("sheet_name", sa.String(), nullable=True),
        sa.Column("encoding", sa.String(), nullable=False, server_default="utf-8"),
        sa.Column("delimiter", sa.String(), nullable=False, server_default=","),
        sa.Column("uploaded_by", UUID(as_uuid=True), nullable=True),
        sa.Column("rows_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_valid", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_invalid", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_rows", JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("mapping", JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("options", JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("counters", JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("errors", JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("catalog_imports")
