import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_sales_cash_registers"
down_revision = "0006_cash_receipts"
branch_labels = None
depends_on = None


payment_provider = sa.Enum("cash", "card", "external", name="paymentprovider")
payment_status = sa.Enum("pending", "confirmed", "cancelled", name="paymentstatus")
payment_provider_column = sa.Enum("cash", "card", "external", name="paymentprovider", create_type=False)
payment_status_column = sa.Enum("pending", "confirmed", "cancelled", name="paymentstatus", create_type=False)


def upgrade() -> None:
    op.create_table(
        "cash_registers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        if_not_exists=True,
    )
    op.create_index("ix_cash_registers_active", "cash_registers", ["is_active"], if_not_exists=True)

    payment_provider.create(op.get_bind(), checkfirst=True)
    payment_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("sale_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, server_default=""),
        sa.Column("method", payment_provider_column, nullable=False),
        sa.Column("status", payment_status_column, nullable=False, server_default="pending"),
        sa.Column("reference", sa.String(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        if_not_exists=True,
    )
    op.create_index("ix_payments_status", "payments", ["status"], if_not_exists=True)

    op.create_table(
        "refunds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("sale_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason", sa.String(), nullable=False, server_default=""),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_table("refunds", if_exists=True)
    op.drop_index("ix_payments_status", table_name="payments", if_exists=True)
    op.drop_table("payments", if_exists=True)
    payment_status.drop(op.get_bind(), checkfirst=True)
    payment_provider.drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_cash_registers_active", table_name="cash_registers", if_exists=True)
    op.drop_table("cash_registers", if_exists=True)
