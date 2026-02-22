"""Add public catalog variants/hide flag and public orders.

Revision ID: tenant_0016
Revises: tenant_0015
Create Date: 2026-02-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "tenant_0016"
down_revision = "tenant_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("products", sa.Column("variant_group", sa.String(), nullable=True))
    op.add_column("products", sa.Column("variant_name", sa.String(), nullable=True))

    op.create_table(
        "public_orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("customer_name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "public_order_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("public_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="SET NULL"), nullable=True),
        sa.Column("product_name", sa.String(), nullable=False),
        sa.Column("qty", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("public_order_items")
    op.drop_table("public_orders")
    op.drop_column("products", "variant_name")
    op.drop_column("products", "variant_group")
    op.drop_column("products", "is_hidden")
