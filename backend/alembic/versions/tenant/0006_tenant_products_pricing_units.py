"""Update product pricing, units, and constraints.

Revision ID: tenant_0006
Revises: tenant_0005
Create Date: 2025-10-13 00:00:00.000000
"""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "tenant_0006"
down_revision = "tenant_0005"
branch_labels = None
depends_on = None


def _ensure_placeholder(connection, table_name: str, name: str) -> uuid.UUID:
    existing = connection.execute(
        sa.text(f"SELECT id FROM {table_name} WHERE name = :name"),
        {"name": name},
    ).scalar()
    if existing:
        return existing
    placeholder_id = uuid.uuid4()
    connection.execute(
        sa.text(f"INSERT INTO {table_name} (id, name, is_active) VALUES (:id, :name, true)"),
        {"id": placeholder_id, "name": name},
    )
    return placeholder_id


def upgrade() -> None:
    connection = op.get_bind()
    product_unit = sa.Enum("pcs", "ml", "g", name="product_unit", create_type=False)
    product_unit.create(connection, checkfirst=True)

    op.add_column("products", sa.Column("barcode", sa.String(), nullable=True))
    op.add_column(
        "products",
        sa.Column("unit", product_unit, nullable=False, server_default=sa.text("'pcs'::product_unit")),
    )
    op.add_column(
        "products",
        sa.Column("purchase_price", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "products",
        sa.Column("sell_price", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "products",
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=False, server_default="0"),
    )

    op.alter_column("products", "sku", existing_type=sa.String(), nullable=True)

    op.execute("UPDATE products SET purchase_price = last_purchase_unit_cost, sell_price = price")

    placeholder_category_id = _ensure_placeholder(connection, "categories", "Uncategorized")
    placeholder_brand_id = _ensure_placeholder(connection, "brands", "Unbranded")

    connection.execute(
        sa.text("UPDATE products SET category_id = :category_id WHERE category_id IS NULL"),
        {"category_id": placeholder_category_id},
    )
    connection.execute(
        sa.text("UPDATE products SET brand_id = :brand_id WHERE brand_id IS NULL"),
        {"brand_id": placeholder_brand_id},
    )

    connection.execute(
        sa.text(
            """
            INSERT INTO category_brands (category_id, brand_id)
            SELECT DISTINCT category_id, brand_id
            FROM products
            WHERE category_id IS NOT NULL AND brand_id IS NOT NULL
            ON CONFLICT DO NOTHING
            """
        )
    )

    op.alter_column("products", "category_id", existing_type=UUID(as_uuid=True), nullable=False)
    op.alter_column("products", "brand_id", existing_type=UUID(as_uuid=True), nullable=False)

    op.drop_column("products", "price")
    op.drop_column("products", "last_purchase_unit_cost")

    op.alter_column("products", "unit", server_default=None)
    op.alter_column("products", "purchase_price", server_default=None)
    op.alter_column("products", "sell_price", server_default=None)
    op.alter_column("products", "tax_rate", server_default=None)


def downgrade() -> None:
    connection = op.get_bind()
    product_unit = sa.Enum("pcs", "ml", "g", name="product_unit", create_type=False)

    op.add_column("products", sa.Column("price", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column(
        "products",
        sa.Column("last_purchase_unit_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
    )

    op.execute("UPDATE products SET price = sell_price, last_purchase_unit_cost = purchase_price")

    op.alter_column("products", "sku", existing_type=sa.String(), nullable=False)
    op.alter_column("products", "category_id", existing_type=UUID(as_uuid=True), nullable=True)
    op.alter_column("products", "brand_id", existing_type=UUID(as_uuid=True), nullable=True)

    op.drop_column("products", "tax_rate")
    op.drop_column("products", "sell_price")
    op.drop_column("products", "purchase_price")
    op.drop_column("products", "unit")
    op.drop_column("products", "barcode")

    op.alter_column("products", "price", server_default=None)
    op.alter_column("products", "last_purchase_unit_cost", server_default=None)

    connection.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM pg_type t
                    JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE t.typname = 'product_unit'
                      AND n.nspname = current_schema()
                ) THEN
                    EXECUTE format('DROP TYPE %I.%I', current_schema(), 'product_unit');
                END IF;
            END
            $$;
            """
        )
    )
