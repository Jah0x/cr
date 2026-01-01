import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010_multi_tenant_entities"
down_revision = "0009_users_roles_tenant"
branch_labels = None
depends_on = None


def _default_tenant_id(conn):
    tenant_id = str(uuid.uuid4())
    existing = conn.execute(sa.text("SELECT id FROM tenants WHERE code = :code"), {"code": "default"}).scalar()
    if existing:
        return str(existing)
    conn.execute(
        sa.text(
            "INSERT INTO tenants (id, name, code, status, created_at, updated_at) "
            "VALUES (:id, :name, :code, 'active', timezone('utc', now()), timezone('utc', now()))"
        ),
        {"id": tenant_id, "name": "Default", "code": "default"},
    )
    return tenant_id


def upgrade() -> None:
    conn = op.get_bind()
    tenant_id = _default_tenant_id(conn)

    op.add_column("categories", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("brands", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("product_lines", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("products", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("suppliers", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("purchase_invoices", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("purchase_items", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("stock_moves", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("stock_batches", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("sale_item_cost_allocations", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("sales", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("sale_items", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("payments", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("refunds", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("cash_receipts", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("cash_registers", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))

    tables = [
        "categories",
        "brands",
        "product_lines",
        "products",
        "suppliers",
        "purchase_invoices",
        "purchase_items",
        "stock_moves",
        "stock_batches",
        "sale_item_cost_allocations",
        "sales",
        "sale_items",
        "payments",
        "refunds",
        "cash_receipts",
        "cash_registers",
    ]
    for table in tables:
        conn.execute(
            sa.text(f"UPDATE {table} SET tenant_id = :tenant_id WHERE tenant_id IS NULL"), {"tenant_id": tenant_id}
        )

    for table in tables:
        op.alter_column(table, "tenant_id", nullable=False)

    op.drop_constraint("categories_name_key", "categories", type_="unique")
    op.drop_constraint("brands_name_key", "brands", type_="unique")
    op.drop_constraint("products_sku_key", "products", type_="unique")
    op.drop_constraint("cash_receipts_receipt_id_key", "cash_receipts", type_="unique")
    op.drop_constraint("cash_registers_name_key", "cash_registers", type_="unique")

    op.create_foreign_key("fk_categories_tenant_id", "categories", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_brands_tenant_id", "brands", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_product_lines_tenant_id", "product_lines", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_products_tenant_id", "products", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_suppliers_tenant_id", "suppliers", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_purchase_invoices_tenant_id", "purchase_invoices", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_purchase_items_tenant_id", "purchase_items", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_stock_moves_tenant_id", "stock_moves", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_stock_batches_tenant_id", "stock_batches", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key(
        "fk_sale_item_cost_allocations_tenant_id",
        "sale_item_cost_allocations",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key("fk_sales_tenant_id", "sales", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_sale_items_tenant_id", "sale_items", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_payments_tenant_id", "payments", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_refunds_tenant_id", "refunds", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_cash_receipts_tenant_id", "cash_receipts", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_cash_registers_tenant_id", "cash_registers", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")

    op.create_index("ix_categories_tenant_id", "categories", ["tenant_id"], unique=False)
    op.create_index("ix_categories_name_tenant", "categories", ["name", "tenant_id"], unique=True)
    op.create_index("ix_brands_tenant_id", "brands", ["tenant_id"], unique=False)
    op.create_index("ix_brands_name_tenant", "brands", ["name", "tenant_id"], unique=True)
    op.create_index("ix_product_lines_tenant_id", "product_lines", ["tenant_id"], unique=False)
    op.create_index("ix_products_tenant_id", "products", ["tenant_id"], unique=False)
    op.create_index("ix_products_sku_tenant", "products", ["sku", "tenant_id"], unique=True)
    op.create_index("ix_suppliers_tenant_id", "suppliers", ["tenant_id"], unique=False)
    op.create_index("ix_purchase_invoices_tenant_id", "purchase_invoices", ["tenant_id"], unique=False)
    op.create_index("ix_purchase_items_tenant_id", "purchase_items", ["tenant_id"], unique=False)
    op.create_index("ix_stock_moves_tenant_id", "stock_moves", ["tenant_id"], unique=False)
    op.create_index("ix_stock_batches_tenant_id", "stock_batches", ["tenant_id"], unique=False)
    op.create_index("ix_sale_item_cost_allocations_tenant_id", "sale_item_cost_allocations", ["tenant_id"], unique=False)
    op.create_index("ix_sales_tenant_id", "sales", ["tenant_id"], unique=False)
    op.create_index("ix_sale_items_tenant_id", "sale_items", ["tenant_id"], unique=False)
    op.create_index("ix_payments_tenant_id", "payments", ["tenant_id"], unique=False)
    op.create_index("ix_refunds_tenant_id", "refunds", ["tenant_id"], unique=False)
    op.create_index("ix_cash_receipts_tenant_id", "cash_receipts", ["tenant_id"], unique=False)
    op.create_index("ix_cash_receipts_receipt_id_tenant", "cash_receipts", ["receipt_id", "tenant_id"], unique=True)
    op.create_index("ix_cash_registers_tenant_id", "cash_registers", ["tenant_id"], unique=False)
    op.create_index("ix_cash_registers_name_tenant", "cash_registers", ["name", "tenant_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_cash_registers_name_tenant", table_name="cash_registers")
    op.drop_index("ix_cash_registers_tenant_id", table_name="cash_registers")
    op.drop_index("ix_cash_receipts_receipt_id_tenant", table_name="cash_receipts")
    op.drop_index("ix_cash_receipts_tenant_id", table_name="cash_receipts")
    op.drop_index("ix_refunds_tenant_id", table_name="refunds")
    op.drop_index("ix_payments_tenant_id", table_name="payments")
    op.drop_index("ix_sale_items_tenant_id", table_name="sale_items")
    op.drop_index("ix_sales_tenant_id", table_name="sales")
    op.drop_index("ix_sale_item_cost_allocations_tenant_id", table_name="sale_item_cost_allocations")
    op.drop_index("ix_stock_batches_tenant_id", table_name="stock_batches")
    op.drop_index("ix_stock_moves_tenant_id", table_name="stock_moves")
    op.drop_index("ix_purchase_items_tenant_id", table_name="purchase_items")
    op.drop_index("ix_purchase_invoices_tenant_id", table_name="purchase_invoices")
    op.drop_index("ix_suppliers_tenant_id", table_name="suppliers")
    op.drop_index("ix_products_sku_tenant", table_name="products")
    op.drop_index("ix_products_tenant_id", table_name="products")
    op.drop_index("ix_product_lines_tenant_id", table_name="product_lines")
    op.drop_index("ix_brands_name_tenant", table_name="brands")
    op.drop_index("ix_brands_tenant_id", table_name="brands")
    op.drop_index("ix_categories_name_tenant", table_name="categories")
    op.drop_index("ix_categories_tenant_id", table_name="categories")

    op.drop_constraint("fk_cash_registers_tenant_id", "cash_registers", type_="foreignkey")
    op.drop_constraint("fk_cash_receipts_tenant_id", "cash_receipts", type_="foreignkey")
    op.drop_constraint("fk_refunds_tenant_id", "refunds", type_="foreignkey")
    op.drop_constraint("fk_payments_tenant_id", "payments", type_="foreignkey")
    op.drop_constraint("fk_sale_items_tenant_id", "sale_items", type_="foreignkey")
    op.drop_constraint("fk_sales_tenant_id", "sales", type_="foreignkey")
    op.drop_constraint("fk_sale_item_cost_allocations_tenant_id", "sale_item_cost_allocations", type_="foreignkey")
    op.drop_constraint("fk_stock_batches_tenant_id", "stock_batches", type_="foreignkey")
    op.drop_constraint("fk_stock_moves_tenant_id", "stock_moves", type_="foreignkey")
    op.drop_constraint("fk_purchase_items_tenant_id", "purchase_items", type_="foreignkey")
    op.drop_constraint("fk_purchase_invoices_tenant_id", "purchase_invoices", type_="foreignkey")
    op.drop_constraint("fk_suppliers_tenant_id", "suppliers", type_="foreignkey")
    op.drop_constraint("fk_products_tenant_id", "products", type_="foreignkey")
    op.drop_constraint("fk_product_lines_tenant_id", "product_lines", type_="foreignkey")
    op.drop_constraint("fk_brands_tenant_id", "brands", type_="foreignkey")
    op.drop_constraint("fk_categories_tenant_id", "categories", type_="foreignkey")

    op.create_unique_constraint("cash_registers_name_key", "cash_registers", ["name"])
    op.create_unique_constraint("cash_receipts_receipt_id_key", "cash_receipts", ["receipt_id"])
    op.create_unique_constraint("products_sku_key", "products", ["sku"])
    op.create_unique_constraint("brands_name_key", "brands", ["name"])
    op.create_unique_constraint("categories_name_key", "categories", ["name"])

    op.drop_column("cash_registers", "tenant_id")
    op.drop_column("cash_receipts", "tenant_id")
    op.drop_column("refunds", "tenant_id")
    op.drop_column("payments", "tenant_id")
    op.drop_column("sale_items", "tenant_id")
    op.drop_column("sales", "tenant_id")
    op.drop_column("sale_item_cost_allocations", "tenant_id")
    op.drop_column("stock_batches", "tenant_id")
    op.drop_column("stock_moves", "tenant_id")
    op.drop_column("purchase_items", "tenant_id")
    op.drop_column("purchase_invoices", "tenant_id")
    op.drop_column("suppliers", "tenant_id")
    op.drop_column("products", "tenant_id")
    op.drop_column("product_lines", "tenant_id")
    op.drop_column("brands", "tenant_id")
    op.drop_column("categories", "tenant_id")
