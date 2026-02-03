"""Restrict category and brand deletion for products.

Revision ID: tenant_0011
Revises: tenant_0010
Create Date: 2025-10-13 00:00:00.000000
"""

from alembic import op

revision = "tenant_0011"
down_revision = "tenant_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("products_category_id_fkey", "products", type_="foreignkey")
    op.drop_constraint("products_brand_id_fkey", "products", type_="foreignkey")
    op.create_foreign_key(
        "products_category_id_fkey",
        "products",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "products_brand_id_fkey",
        "products",
        "brands",
        ["brand_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("products_brand_id_fkey", "products", type_="foreignkey")
    op.drop_constraint("products_category_id_fkey", "products", type_="foreignkey")
    op.create_foreign_key(
        "products_category_id_fkey",
        "products",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "products_brand_id_fkey",
        "products",
        "brands",
        ["brand_id"],
        ["id"],
        ondelete="SET NULL",
    )
