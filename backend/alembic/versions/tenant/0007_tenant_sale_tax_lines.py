"""Add sale tax lines table.

Revision ID: tenant_0007
Revises: tenant_0006
Create Date: 2025-10-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID

revision = "tenant_0007"
down_revision = "tenant_0006"
branch_labels = None
depends_on = None

payment_provider_enum = ENUM("cash", "card", "transfer", name="paymentprovider", create_type=False)


def upgrade() -> None:
    payment_provider_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "sale_tax_lines",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("sale_id", UUID(as_uuid=True), sa.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_id", sa.String(), nullable=False),
        sa.Column("rule_name", sa.String(), nullable=False),
        sa.Column("rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("method", payment_provider_enum, nullable=True),
        sa.Column("taxable_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sale_tax_lines_sale_id", "sale_tax_lines", ["sale_id"])
    op.create_index("ix_sale_tax_lines_rule_id", "sale_tax_lines", ["rule_id"])
    op.create_index("ix_sale_tax_lines_method", "sale_tax_lines", ["method"])


def downgrade() -> None:
    op.drop_index("ix_sale_tax_lines_method", table_name="sale_tax_lines")
    op.drop_index("ix_sale_tax_lines_rule_id", table_name="sale_tax_lines")
    op.drop_index("ix_sale_tax_lines_sale_id", table_name="sale_tax_lines")
    op.drop_table("sale_tax_lines")
