"""Add stores and link core operations to store.

Revision ID: tenant_0013
Revises: tenant_0012
Create Date: 2026-02-05 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

revision = "tenant_0013"
down_revision = "tenant_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_stores_name", "stores", ["name"], unique=True)

    stores_table = sa.table(
        "stores",
        sa.column("id", UUID(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("is_default", sa.Boolean()),
    )
    op.bulk_insert(
        stores_table,
        [{"id": uuid.uuid4(), "name": "Основная точка", "is_default": True}],
    )

    op.add_column("sales", sa.Column("store_id", UUID(as_uuid=True), nullable=True))
    op.add_column("expenses", sa.Column("store_id", UUID(as_uuid=True), nullable=True))
    op.add_column("stock_moves", sa.Column("store_id", UUID(as_uuid=True), nullable=True))

    op.create_foreign_key("fk_sales_store_id_stores", "sales", "stores", ["store_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_expenses_store_id_stores", "expenses", "stores", ["store_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_stock_moves_store_id_stores", "stock_moves", "stores", ["store_id"], ["id"], ondelete="RESTRICT")

    op.execute(
        """
        UPDATE sales
        SET store_id = s.id
        FROM stores s
        WHERE s.is_default = true AND sales.store_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE expenses
        SET store_id = s.id
        FROM stores s
        WHERE s.is_default = true AND expenses.store_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE stock_moves
        SET store_id = s.id
        FROM stores s
        WHERE s.is_default = true AND stock_moves.store_id IS NULL
        """
    )

    op.alter_column("sales", "store_id", nullable=False)
    op.alter_column("expenses", "store_id", nullable=False)


def downgrade() -> None:
    op.drop_constraint("fk_stock_moves_store_id_stores", "stock_moves", type_="foreignkey")
    op.drop_constraint("fk_expenses_store_id_stores", "expenses", type_="foreignkey")
    op.drop_constraint("fk_sales_store_id_stores", "sales", type_="foreignkey")

    op.drop_column("stock_moves", "store_id")
    op.drop_column("expenses", "store_id")
    op.drop_column("sales", "store_id")

    op.drop_index("ix_stores_name", table_name="stores")
    op.drop_table("stores")
