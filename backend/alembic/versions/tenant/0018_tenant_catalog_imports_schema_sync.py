"""Align catalog_imports schema with application model.

Revision ID: tenant_0018
Revises: tenant_0017
Create Date: 2026-03-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "tenant_0018"
down_revision = "tenant_0017"
branch_labels = None
depends_on = None


def _has_column(columns: set[str], name: str) -> bool:
    return name in columns


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("catalog_imports")}

    if _has_column(columns, "total_rows") and not _has_column(columns, "rows_total"):
        op.alter_column("catalog_imports", "total_rows", new_column_name="rows_total")
        columns.remove("total_rows")
        columns.add("rows_total")

    if _has_column(columns, "failed_count") and not _has_column(columns, "rows_invalid"):
        op.alter_column("catalog_imports", "failed_count", new_column_name="rows_invalid")
        columns.remove("failed_count")
        columns.add("rows_invalid")

    if _has_column(columns, "error_log") and not _has_column(columns, "errors"):
        op.alter_column("catalog_imports", "error_log", new_column_name="errors")
        columns.remove("error_log")
        columns.add("errors")

    if not _has_column(columns, "mode"):
        op.add_column(
            "catalog_imports",
            sa.Column("mode", sa.String(), nullable=False, server_default="sync"),
        )

    if not _has_column(columns, "sheet_name"):
        op.add_column("catalog_imports", sa.Column("sheet_name", sa.String(), nullable=True))

    if not _has_column(columns, "encoding"):
        op.add_column(
            "catalog_imports",
            sa.Column("encoding", sa.String(), nullable=False, server_default="utf-8"),
        )

    if not _has_column(columns, "delimiter"):
        op.add_column(
            "catalog_imports",
            sa.Column("delimiter", sa.String(), nullable=False, server_default=","),
        )

    if not _has_column(columns, "rows_total"):
        op.add_column(
            "catalog_imports",
            sa.Column("rows_total", sa.Integer(), nullable=False, server_default="0"),
        )

    if not _has_column(columns, "rows_invalid"):
        op.add_column(
            "catalog_imports",
            sa.Column("rows_invalid", sa.Integer(), nullable=False, server_default="0"),
        )

    if not _has_column(columns, "rows_valid"):
        op.add_column("catalog_imports", sa.Column("rows_valid", sa.Integer(), nullable=True))

    if not _has_column(columns, "source_rows"):
        op.add_column(
            "catalog_imports",
            sa.Column("source_rows", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        )

    if not _has_column(columns, "mapping"):
        op.add_column(
            "catalog_imports",
            sa.Column("mapping", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        )

    if not _has_column(columns, "options"):
        op.add_column(
            "catalog_imports",
            sa.Column("options", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        )

    if not _has_column(columns, "counters"):
        op.add_column(
            "catalog_imports",
            sa.Column("counters", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        )

    if not _has_column(columns, "errors"):
        op.add_column(
            "catalog_imports",
            sa.Column("errors", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        )

    if not _has_column(columns, "started_at"):
        op.add_column("catalog_imports", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))

    if not _has_column(columns, "finished_at"):
        op.add_column("catalog_imports", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))

    op.execute(
        """
        UPDATE catalog_imports
        SET rows_valid = GREATEST(COALESCE(rows_total, 0) - COALESCE(rows_invalid, 0), 0)
        WHERE rows_valid IS NULL
        """
    )

    op.execute("UPDATE catalog_imports SET filename = 'uploaded.csv' WHERE filename IS NULL")

    op.alter_column("catalog_imports", "filename", existing_type=sa.Text(), type_=sa.String(), nullable=False)
    op.alter_column("catalog_imports", "status", existing_type=sa.Text(), type_=sa.String(), nullable=False)
    op.alter_column("catalog_imports", "mode", existing_type=sa.String(), nullable=False, server_default="sync")
    op.alter_column("catalog_imports", "encoding", existing_type=sa.String(), nullable=False, server_default="utf-8")
    op.alter_column("catalog_imports", "delimiter", existing_type=sa.String(), nullable=False, server_default=",")
    op.alter_column("catalog_imports", "rows_total", existing_type=sa.Integer(), nullable=False, server_default="0")
    op.alter_column("catalog_imports", "rows_valid", existing_type=sa.Integer(), nullable=False, server_default="0")
    op.alter_column("catalog_imports", "rows_invalid", existing_type=sa.Integer(), nullable=False, server_default="0")

    if "ix_catalog_imports_tenant_code" in {idx["name"] for idx in inspector.get_indexes("catalog_imports")}:
        op.drop_index("ix_catalog_imports_tenant_code", table_name="catalog_imports")

    refreshed_columns = {column["name"] for column in sa.inspect(bind).get_columns("catalog_imports")}
    for legacy_column in {"tenant_code", "created_count", "updated_count", "updated_at"}:
        if legacy_column in refreshed_columns:
            op.drop_column("catalog_imports", legacy_column)


def downgrade() -> None:
    op.add_column("catalog_imports", sa.Column("tenant_code", sa.Text(), nullable=False, server_default="default"))
    op.add_column("catalog_imports", sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("catalog_imports", sa.Column("updated_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column(
        "catalog_imports",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_catalog_imports_tenant_code", "catalog_imports", ["tenant_code"], unique=False)

    op.drop_column("catalog_imports", "finished_at")
    op.drop_column("catalog_imports", "started_at")
    op.drop_column("catalog_imports", "counters")
    op.drop_column("catalog_imports", "options")
    op.drop_column("catalog_imports", "mapping")
    op.drop_column("catalog_imports", "source_rows")
    op.drop_column("catalog_imports", "rows_valid")
    op.drop_column("catalog_imports", "sheet_name")
    op.drop_column("catalog_imports", "mode")

    op.alter_column("catalog_imports", "rows_total", new_column_name="total_rows")
    op.alter_column("catalog_imports", "rows_invalid", new_column_name="failed_count")
    op.alter_column("catalog_imports", "errors", new_column_name="error_log")
