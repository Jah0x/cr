"""Add category-brand links.

Revision ID: tenant_0005
Revises: tenant_0004
Create Date: 2025-10-02 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "tenant_0005"
down_revision = "tenant_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "category_brands",
        sa.Column("category_id", UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("category_id", "brand_id"),
        sa.UniqueConstraint("category_id", "brand_id", name="uq_category_brands_category_id_brand_id"),
    )


def downgrade() -> None:
    op.drop_table("category_brands")
