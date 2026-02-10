"""Add recurring expenses and accruals.

Revision ID: tenant_0015
Revises: tenant_0014
Create Date: 2026-02-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "tenant_0015"
down_revision = "tenant_0014"
branch_labels = None
depends_on = None


recurring_expense_period_enum = sa.Enum(
    "daily", "weekly", "monthly", name="recurringexpenseperiod", create_type=False
)
recurring_expense_allocation_method_enum = sa.Enum(
    "calendar_days", "fixed_30", name="recurringexpenseallocationmethod", create_type=False
)


def upgrade() -> None:
    recurring_expense_period_enum.create(op.get_bind(), checkfirst=True)
    recurring_expense_allocation_method_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "recurring_expenses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("store_id", UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("period", recurring_expense_period_enum, nullable=False),
        sa.Column(
            "allocation_method",
            recurring_expense_allocation_method_enum,
            nullable=False,
            server_default=sa.text("'calendar_days'::recurringexpenseallocationmethod"),
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "expense_accruals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("store_id", UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "recurring_expense_id",
            UUID(as_uuid=True),
            sa.ForeignKey("recurring_expenses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("recurring_expense_id", "date", name="uq_expense_accruals_recurring_expense_id_date"),
    )
    op.create_index("ix_expense_accruals_store_id_date", "expense_accruals", ["store_id", "date"])


def downgrade() -> None:
    op.drop_index("ix_expense_accruals_store_id_date", table_name="expense_accruals")
    op.drop_table("expense_accruals")
    op.drop_table("recurring_expenses")

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM pg_type t
                    JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE t.typname = 'recurringexpenseallocationmethod'
                      AND n.nspname = current_schema()
                ) THEN
                    EXECUTE format('DROP TYPE %I.%I', current_schema(), 'recurringexpenseallocationmethod');
                END IF;
            END
            $$;
            """
        )
    )
    connection.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM pg_type t
                    JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE t.typname = 'recurringexpenseperiod'
                      AND n.nspname = current_schema()
                ) THEN
                    EXECUTE format('DROP TYPE %I.%I', current_schema(), 'recurringexpenseperiod');
                END IF;
            END
            $$;
            """
        )
    )
