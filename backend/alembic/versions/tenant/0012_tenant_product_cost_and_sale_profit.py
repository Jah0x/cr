"""Add product cost price and sale item profit fields.

Revision ID: tenant_0012
Revises: tenant_0011
Create Date: 2025-10-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "tenant_0012"
down_revision = "tenant_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("cost_price", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "sale_items",
        sa.Column("cost_snapshot", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "sale_items",
        sa.Column("profit_line", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("sale_items", "profit_line")
    op.drop_column("sale_items", "cost_snapshot")
    op.drop_column("products", "cost_price")
