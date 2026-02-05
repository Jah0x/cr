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


cashier_shift_status_enum = sa.Enum("open", "closed", name="cashiershiftstatus")


def upgrade() -> None:
    cashier_shift_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "cashier_shifts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("store_id", UUID(as_uuid=True), sa.ForeignKey("stores.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cashier_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", cashier_shift_status_enum, nullable=False, server_default="open"),
        sa.Column("opening_cash", sa.Numeric(12, 2), nullable=False, server_default="0"),
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

    cashier_shift_status_enum.drop(op.get_bind(), checkfirst=True)
