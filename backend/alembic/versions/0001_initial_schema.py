"""Initial schema.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2025-09-27 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ENUM

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

purchase_status_enum = ENUM("draft", "posted", "void", name="purchasestatus", create_type=False)
sale_status_enum = ENUM("completed", "void", name="salestatus", create_type=False)
payment_provider_enum = ENUM("cash", "card", "external", name="paymentprovider", create_type=False)
payment_status_enum = ENUM("pending", "confirmed", "cancelled", name="paymentstatus", create_type=False)
tenant_status_enum = ENUM("active", "inactive", name="tenantstatus", create_type=False)


def upgrade() -> None:
    ENUM("draft", "posted", "void", name="purchasestatus").create(op.get_bind(), checkfirst=True)
    ENUM("completed", "void", name="salestatus").create(op.get_bind(), checkfirst=True)
    ENUM("cash", "card", "external", name="paymentprovider").create(op.get_bind(), checkfirst=True)
    ENUM("pending", "confirmed", "cancelled", name="paymentstatus").create(op.get_bind(), checkfirst=True)
    ENUM("active", "inactive", name="tenantstatus").create(op.get_bind(), checkfirst=True)

    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("status", tenant_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "brands",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "product_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "line_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_lines.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("last_purchase_unit_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "suppliers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("contact", sa.String(), nullable=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "purchase_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "supplier_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("suppliers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", purchase_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "purchase_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "invoice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("purchase_invoices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "stock_moves",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("delta_qty", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("reference", sa.String(), nullable=True),
        sa.Column("ref_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "stock_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "purchase_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("purchase_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "sales",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sale_status_enum, nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "sale_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "sale_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sales.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("qty", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "sale_item_cost_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "sale_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sale_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("stock_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "sale_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sales.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("method", payment_provider_enum, nullable=False),
        sa.Column("status", payment_status_enum, nullable=False),
        sa.Column("reference", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "refunds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "sale_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sales.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "cash_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "sale_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sales.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("receipt_id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_table(
        "cash_registers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )

    op.create_index("ix_tenants_status", "tenants", ["status"], unique=False)
    op.create_unique_constraint("tenants_code_key", "tenants", ["code"])

    op.create_index("ix_users_email_tenant", "users", ["email", "tenant_id"], unique=True)
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"], unique=False)

    op.create_index("ix_roles_name_tenant", "roles", ["name", "tenant_id"], unique=True)
    op.create_index("ix_roles_tenant_id", "roles", ["tenant_id"], unique=False)

    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"], unique=False)
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"], unique=False)
    op.create_index("ix_user_roles_tenant_id", "user_roles", ["tenant_id"], unique=False)

    op.create_index("ix_categories_name_tenant", "categories", ["name", "tenant_id"], unique=True)
    op.create_index("ix_categories_tenant_id", "categories", ["tenant_id"], unique=False)

    op.create_index("ix_brands_name_tenant", "brands", ["name", "tenant_id"], unique=True)
    op.create_index("ix_brands_tenant_id", "brands", ["tenant_id"], unique=False)

    op.create_index("ix_product_lines_tenant_id", "product_lines", ["tenant_id"], unique=False)

    op.create_index("ix_products_sku_tenant", "products", ["sku", "tenant_id"], unique=True)
    op.create_index("ix_products_tenant_id", "products", ["tenant_id"], unique=False)

    op.create_index("ix_suppliers_tenant_id", "suppliers", ["tenant_id"], unique=False)
    op.create_index("ix_purchase_invoices_tenant_id", "purchase_invoices", ["tenant_id"], unique=False)
    op.create_index("ix_purchase_items_tenant_id", "purchase_items", ["tenant_id"], unique=False)

    op.create_index("ix_stock_moves_tenant_id", "stock_moves", ["tenant_id"], unique=False)
    op.create_index("ix_stock_batches_tenant_id", "stock_batches", ["tenant_id"], unique=False)
    op.create_index(
        "ix_sale_item_cost_allocations_tenant_id",
        "sale_item_cost_allocations",
        ["tenant_id"],
        unique=False,
    )

    op.create_index("ix_sales_status", "sales", ["status"], unique=False)
    op.create_index("ix_sales_tenant_id", "sales", ["tenant_id"], unique=False)

    op.create_index("ix_sale_items_sale_id", "sale_items", ["sale_id"], unique=False)
    op.create_index("ix_sale_items_product_id", "sale_items", ["product_id"], unique=False)
    op.create_index("ix_sale_items_tenant_id", "sale_items", ["tenant_id"], unique=False)

    op.create_index("ix_payments_status", "payments", ["status"], unique=False)
    op.create_index("ix_payments_tenant_id", "payments", ["tenant_id"], unique=False)

    op.create_index("ix_refunds_tenant_id", "refunds", ["tenant_id"], unique=False)

    op.create_index("ix_cash_receipts_receipt_id_tenant", "cash_receipts", ["receipt_id", "tenant_id"], unique=True)
    op.create_index("ix_cash_receipts_tenant_id", "cash_receipts", ["tenant_id"], unique=False)

    op.create_index("ix_cash_registers_active", "cash_registers", ["is_active"], unique=False)
    op.create_index("ix_cash_registers_name_tenant", "cash_registers", ["name", "tenant_id"], unique=True)
    op.create_index("ix_cash_registers_tenant_id", "cash_registers", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_cash_registers_tenant_id", table_name="cash_registers")
    op.drop_index("ix_cash_registers_name_tenant", table_name="cash_registers")
    op.drop_index("ix_cash_registers_active", table_name="cash_registers")
    op.drop_index("ix_cash_receipts_tenant_id", table_name="cash_receipts")
    op.drop_index("ix_cash_receipts_receipt_id_tenant", table_name="cash_receipts")
    op.drop_index("ix_refunds_tenant_id", table_name="refunds")
    op.drop_index("ix_payments_tenant_id", table_name="payments")
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_sale_items_tenant_id", table_name="sale_items")
    op.drop_index("ix_sale_items_product_id", table_name="sale_items")
    op.drop_index("ix_sale_items_sale_id", table_name="sale_items")
    op.drop_index("ix_sales_tenant_id", table_name="sales")
    op.drop_index("ix_sales_status", table_name="sales")
    op.drop_index(
        "ix_sale_item_cost_allocations_tenant_id",
        table_name="sale_item_cost_allocations",
    )
    op.drop_index("ix_stock_batches_tenant_id", table_name="stock_batches")
    op.drop_index("ix_stock_moves_tenant_id", table_name="stock_moves")
    op.drop_index("ix_purchase_items_tenant_id", table_name="purchase_items")
    op.drop_index("ix_purchase_invoices_tenant_id", table_name="purchase_invoices")
    op.drop_index("ix_suppliers_tenant_id", table_name="suppliers")
    op.drop_index("ix_products_tenant_id", table_name="products")
    op.drop_index("ix_products_sku_tenant", table_name="products")
    op.drop_index("ix_product_lines_tenant_id", table_name="product_lines")
    op.drop_index("ix_brands_tenant_id", table_name="brands")
    op.drop_index("ix_brands_name_tenant", table_name="brands")
    op.drop_index("ix_categories_tenant_id", table_name="categories")
    op.drop_index("ix_categories_name_tenant", table_name="categories")
    op.drop_index("ix_user_roles_tenant_id", table_name="user_roles")
    op.drop_index("ix_user_roles_role_id", table_name="user_roles")
    op.drop_index("ix_user_roles_user_id", table_name="user_roles")
    op.drop_index("ix_roles_tenant_id", table_name="roles")
    op.drop_index("ix_roles_name_tenant", table_name="roles")
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_index("ix_users_email_tenant", table_name="users")
    op.drop_constraint("tenants_code_key", "tenants", type_="unique")
    op.drop_index("ix_tenants_status", table_name="tenants")

    op.drop_table("cash_registers")
    op.drop_table("cash_receipts")
    op.drop_table("refunds")
    op.drop_table("payments")
    op.drop_table("sale_item_cost_allocations")
    op.drop_table("sale_items")
    op.drop_table("sales")
    op.drop_table("stock_batches")
    op.drop_table("stock_moves")
    op.drop_table("purchase_items")
    op.drop_table("purchase_invoices")
    op.drop_table("suppliers")
    op.drop_table("products")
    op.drop_table("product_lines")
    op.drop_table("brands")
    op.drop_table("categories")
    op.drop_table("user_roles")
    op.drop_table("roles")
    op.drop_table("users")
    op.drop_table("tenants")

    ENUM("draft", "posted", "void", name="purchasestatus").drop(op.get_bind(), checkfirst=True)
    ENUM("completed", "void", name="salestatus").drop(op.get_bind(), checkfirst=True)
    ENUM("cash", "card", "external", name="paymentprovider").drop(op.get_bind(), checkfirst=True)
    ENUM("pending", "confirmed", "cancelled", name="paymentstatus").drop(op.get_bind(), checkfirst=True)
    ENUM("active", "inactive", name="tenantstatus").drop(op.get_bind(), checkfirst=True)
