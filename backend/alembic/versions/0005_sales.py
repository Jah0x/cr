import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0005_sales"
down_revision = "0004_users_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sale_status = sa.Enum("completed", "void", name="salestatus")
    sale_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "sales",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("status", sale_status, nullable=False, server_default="completed"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(), server_default=""),
    )
    op.create_index("ix_sales_status", "sales", ["status"])
    op.create_table(
        "sale_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("sale_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sales.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("qty", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
    )
    op.create_index("ix_sale_items_sale_id", "sale_items", ["sale_id"])
    op.create_index("ix_sale_items_product_id", "sale_items", ["product_id"])
    op.add_column("stock_moves", sa.Column("delta_qty", sa.Numeric(12, 3), server_default="0", nullable=False))
    op.add_column("stock_moves", sa.Column("ref_id", postgresql.UUID(as_uuid=True)))
    op.add_column("stock_moves", sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")))
    op.execute("UPDATE stock_moves SET delta_qty = quantity")


def downgrade() -> None:
    op.drop_column("stock_moves", "created_by_user_id")
    op.drop_column("stock_moves", "ref_id")
    op.drop_column("stock_moves", "delta_qty")
    op.drop_index("ix_sale_items_product_id", table_name="sale_items")
    op.drop_index("ix_sale_items_sale_id", table_name="sale_items")
    op.drop_table("sale_items")
    op.drop_index("ix_sales_status", table_name="sales")
    op.drop_table("sales")
    sale_status = sa.Enum("completed", "void", name="salestatus")
    sale_status.drop(op.get_bind(), checkfirst=True)
