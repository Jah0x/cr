import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0006_cash_receipts"
down_revision = "0005_sales"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cash_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("sale_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False),
        sa.Column("receipt_id", sa.String(), nullable=False, unique=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("payload_json", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_table("cash_receipts", if_exists=True)
