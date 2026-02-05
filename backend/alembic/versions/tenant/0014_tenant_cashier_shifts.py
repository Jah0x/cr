"""Add cashier shifts and link sales to shifts.

Revision ID: tenant_0014
Revises: tenant_0013
Create Date: 2026-02-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "tenant_0014"
down_revision = "tenant_0013"
branch_labels = None
depends_on = None


cashier_shift_status_enum = sa.Enum("open", "closed", name="cashiershiftstatus", create_type=False)


def _create_enum_if_not_exists(enum_name: str, values: tuple[str, ...]) -> None:
    quoted_values = ", ".join("'%s'" % value.replace("'", "''") for value in values)
    # Создаём тип **в текущей схеме** (tenant) только если его там нет.
    op.execute(
        sa.text(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_type t
                    JOIN pg_namespace n ON t.typnamespace = n.oid
                    WHERE t.typname = '{enum_name}'
                      AND n.nspname = current_schema()
                ) THEN
                    EXECUTE 'CREATE TYPE ' || quote_ident(current_schema()) || '.' || quote_ident('{enum_name}') || ' AS ENUM ({quoted_values})';
                END IF;
            END $$;
            """
        )
    )


def upgrade() -> None:
    _create_enum_if_not_exists("cashiershiftstatus", ("open", "closed"))

    op.create_table(
        "cashier_shifts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("store_id", UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cashier_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", cashier_shift_status_enum, nullable=False, server_default=sa.text("'open'::cashiershiftstatus")),
        sa.Column("opening_cash", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("closing_cash", sa.Numeric(12, 2), nullable=True),
        sa.Column("note", sa.String(), nullable=True),
    )
    op.create_index("ix_cashier_shifts_cashier_id_status", "cashier_shifts", ["cashier_id", "status"])
    op.create_index("ix_cashier_shifts_store_id_opened_at", "cashier_shifts", ["store_id", "opened_at"])

    op.add_column("sales", sa.Column("shift_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_sales_shift_id_cashier_shifts",
        "sales",
        "cashier_shifts",
        ["shift_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_sales_shift_id_cashier_shifts", "sales", type_="foreignkey")
    op.drop_column("sales", "shift_id")

    op.drop_index("ix_cashier_shifts_store_id_opened_at", table_name="cashier_shifts")
    op.drop_index("ix_cashier_shifts_cashier_id_status", table_name="cashier_shifts")
    op.drop_table("cashier_shifts")

    # Удаляем enum только из текущей (tenant) схемы, если он там есть
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM pg_type t
                    JOIN pg_namespace n ON t.typnamespace = n.oid
                    WHERE t.typname = 'cashiershiftstatus'
                      AND n.nspname = current_schema()
                ) THEN
                    EXECUTE 'DROP TYPE ' || quote_ident(current_schema()) || '.cashiershiftstatus';
                END IF;
            END $$;
            """
        )
    )
