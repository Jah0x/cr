"""Add catalog hierarchy nodes and product mapping.

Revision ID: tenant_0004
Revises: tenant_0003
Create Date: 2025-10-02 00:00:00.000000
"""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "tenant_0004"
down_revision = "tenant_0003"
branch_labels = ("tenant",)
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_nodes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("level_code", sa.String(), nullable=False),
        sa.Column("parent_id", UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("meta", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["parent_id"], ["catalog_nodes.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_catalog_nodes_parent_level", "catalog_nodes", ["parent_id", "level_code"])
    op.create_index(
        "uq_catalog_nodes_parent_level_name",
        "catalog_nodes",
        ["parent_id", "level_code", sa.text("lower(name)")],
        unique=True,
    )
    op.add_column(
        "products",
        sa.Column("hierarchy_node_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_products_hierarchy_node",
        "products",
        "catalog_nodes",
        ["hierarchy_node_id"],
        ["id"],
        ondelete="SET NULL",
    )
    _backfill_catalog_nodes()


def _select_existing_node(conn, level_code, parent_id, name):
    params = {"level_code": level_code, "name": name.lower()}
    if parent_id is None:
        query = "SELECT id FROM catalog_nodes WHERE level_code = :level_code AND parent_id IS NULL AND lower(name) = :name"
    else:
        query = (
            "SELECT id FROM catalog_nodes "
            "WHERE level_code = :level_code AND parent_id = :parent_id AND lower(name) = :name"
        )
        params["parent_id"] = parent_id
    result = conn.execute(sa.text(query), params).fetchone()
    return result[0] if result else None


def _insert_node(conn, level_code, parent_id, name):
    node_id = uuid.uuid4()
    conn.execute(
        sa.text(
            """
            INSERT INTO catalog_nodes (id, level_code, parent_id, name, code, meta, is_active, created_at)
            VALUES (:id, :level_code, :parent_id, :name, NULL, '{}'::jsonb, TRUE, now())
            """
        ),
        {
            "id": node_id,
            "level_code": level_code,
            "parent_id": parent_id,
            "name": name,
        },
    )
    return node_id


def _get_or_create_node(conn, level_code, parent_id, name):
    existing_id = _select_existing_node(conn, level_code, parent_id, name)
    if existing_id:
        return existing_id
    return _insert_node(conn, level_code, parent_id, name)


def _backfill_catalog_nodes():
    conn = op.get_bind()
    brand_rows = conn.execute(sa.text("SELECT id, name FROM brands")).fetchall()
    brand_map = {}
    for brand_id, name in brand_rows:
        node_id = _get_or_create_node(conn, "manufacturer", None, name)
        brand_map[brand_id] = node_id

    line_rows = conn.execute(sa.text("SELECT id, name, brand_id FROM product_lines")).fetchall()
    line_map = {}
    for line_id, name, brand_id in line_rows:
        parent_id = brand_map.get(brand_id)
        if parent_id is None:
            parent_id = _get_or_create_node(conn, "manufacturer", None, f"Brand {brand_id}")
            brand_map[brand_id] = parent_id
        node_id = _get_or_create_node(conn, "model", parent_id, name)
        line_map[line_id] = node_id

    product_rows = conn.execute(sa.text("SELECT id, name, line_id FROM products")).fetchall()
    for product_id, name, line_id in product_rows:
        parent_id = line_map.get(line_id)
        if parent_id is None and line_id is not None:
            line_name = conn.execute(
                sa.text("SELECT name, brand_id FROM product_lines WHERE id = :line_id"),
                {"line_id": line_id},
            ).fetchone()
            if line_name:
                line_name_value, brand_id = line_name
                brand_parent = brand_map.get(brand_id)
                if brand_parent is None:
                    brand_parent = _get_or_create_node(conn, "manufacturer", None, f"Brand {brand_id}")
                    brand_map[brand_id] = brand_parent
                parent_id = _get_or_create_node(conn, "model", brand_parent, line_name_value)
                line_map[line_id] = parent_id
        node_id = _get_or_create_node(conn, "flavor", parent_id, name)
        conn.execute(
            sa.text(
                """
                UPDATE products
                SET hierarchy_node_id = :node_id
                WHERE id = :product_id AND hierarchy_node_id IS NULL
                """
            ),
            {"node_id": node_id, "product_id": product_id},
        )


def downgrade() -> None:
    op.drop_constraint("fk_products_hierarchy_node", "products", type_="foreignkey")
    op.drop_column("products", "hierarchy_node_id")
    op.drop_index("uq_catalog_nodes_parent_level_name", table_name="catalog_nodes")
    op.drop_index("ix_catalog_nodes_parent_level", table_name="catalog_nodes")
    op.drop_table("catalog_nodes")
