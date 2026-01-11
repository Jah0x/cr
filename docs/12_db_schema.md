# Database schema

Alembic revisions (tenant branch unless noted):
- `0001_initial` — authentication tables with seeded roles.
- `0002_catalog` — catalog tables.
- `0003_purchasing_stock` — purchasing and stock tables.
- `0004_users_roles` — role mapping updates.
- `0005_sales` — basic sales tables.
- `0006_cash_receipts` — cash receipt records.
- `0007_sales_cash_registers` — payments, refunds, and cash registers.
- `0008_tenants` — tenant directory table.
- `0002_public_platform` (public branch) — public modules/templates and tenant mapping tables.
- `0004_public_features` (public branch) — public features catalog.

## Tenancy layout
- `public.tenants` stores the tenant directory.
- Each tenant has its own schema, and all tenant-scoped tables live inside that schema.
- Application connections set `search_path` to the tenant schema, so tenant-scoped tables do not store `tenant_id` columns.
- Alembic splits migrations into public (`alembic/versions/public`) and tenant (`alembic/versions/tenant`) branches; use `python -m app.cli migrate-all` to apply both to all tenants.

## users
- `id` — UUID primary key.
- `email` — unique email address within the tenant schema.
- `password_hash` — bcrypt hash.
- `is_active` — boolean flag for login eligibility, defaults to true.
- `created_at` — timezone-aware creation timestamp, defaults to `now()`.
- `last_login_at` — optional timestamp of last login.
- Indexes: `ix_users_email` unique on `email`.

## roles
- `id` — UUID primary key.
- `name` — unique role name within the tenant schema.
- Seeded values: `owner`, `admin`, `cashier`.
- Indexes: `ix_roles_name` unique on `name`.

## user_roles
- `user_id` — references `users.id`, cascade delete.
- `role_id` — references `roles.id`, cascade delete.
- Primary key on (`user_id`, `role_id`).
- Indexes: `ix_user_roles_user_id`, `ix_user_roles_role_id`.

## categories
- `id` — UUID primary key.
- `name` — unique category name.
- `is_active` — boolean flag for enabling/disabling the category.

## brands
- `id` — UUID primary key.
- `name` — unique brand name.
- `is_active` — boolean flag for enabling/disabling the brand.

## product_lines
- `id` — UUID primary key.
- `name` — line label.
- `brand_id` — references `brands.id`, cascade delete.
- `is_active` — boolean flag for enabling/disabling the line.

## products
- `id` — UUID primary key.
- `sku` — unique stock keeping unit.
- `name` — product name.
- `description` — free text description, defaults to empty.
- `image_url` — optional image link.
- `category_id` — nullable reference to `categories.id`, set null on delete.
- `brand_id` — nullable reference to `brands.id`, set null on delete.
- `line_id` — nullable reference to `product_lines.id`, set null on delete.
- `price` — numeric(12,2) price, defaults to 0.
- `last_purchase_unit_cost` — numeric(12,2) last posted purchase unit cost, defaults to 0.
- `is_active` — soft-delete/activation flag, defaults to true.

## suppliers
- `id` — UUID primary key.
- `name` — supplier name.
- `contact` — free-form contact info, defaults to empty string.

## purchase_invoices
- `id` — UUID primary key.
- `supplier_id` — nullable reference to `suppliers.id`, set null on delete.
- `status` — enum(`draft`,`posted`,`void`), defaults to `draft`.
- `created_at` — timezone-aware creation timestamp, defaults to `now()`.

## purchase_items
- `id` — UUID primary key.
- `invoice_id` — references `purchase_invoices.id`, cascade delete.
- `product_id` — references `products.id`, cascade delete.
- `quantity` — numeric(12,3) ordered quantity.
- `unit_cost` — numeric(12,2) cost per unit.

## stock_moves
- `id` — UUID primary key.
- `product_id` — references `products.id`, cascade delete.
- `quantity` — numeric(12,3) snapshot quantity.
- `delta_qty` — numeric(12,3) change applied; defaults to `0`.
- `reason` — reason label such as `purchase`, `sale`, `refund`, `void`, `adjustment`.
- `reference` — free-form reference string, defaults to empty string.
- `ref_id` — optional UUID linking to the source document.
- `created_by_user_id` — nullable reference to `users.id`, set null on delete.
- `created_at` — timezone-aware creation timestamp, defaults to `now()`.
- Behavior: append-only history capturing every inventory change.

## stock_batches
- `id` — UUID primary key.
- `product_id` — references `products.id`, cascade delete.
- `quantity` — numeric(12,3) remaining quantity in batch.
- `unit_cost` — numeric(12,2) unit cost for batch.
- `purchase_item_id` — nullable reference to `purchase_items.id`, set null on delete.

## sale_items
- `id` — UUID primary key.
- `sale_id` — references `sales.id`, cascade delete.
- `product_id` — references `products.id`, set null on delete.
- `qty` — numeric(12,3) quantity sold.
- `unit_price` — numeric(12,2) unit price at sale time.
- `line_total` — numeric(12,2) extended price for the line.
- Indexes: `ix_sale_items_sale_id`, `ix_sale_items_product_id`.

## sales
- `id` — UUID primary key.
- `created_at` — timezone-aware timestamp.
- `created_by_user_id` — nullable reference to `users.id`, set null on delete.
- `status` — enum(`completed`,`void`), defaults to `completed`.
- `total_amount` — numeric(12,2) summed from items.
- `currency` — sale currency code.
- Indexes: `ix_sales_status` on status.

## payments
- `id` — UUID primary key.
- `sale_id` — references `sales.id`, cascade delete.
- `amount` — numeric(12,2) payment amount.
- `currency` — currency code.
- `method` — enum(`cash`,`card`,`external`).
- `status` — enum(`pending`,`confirmed`,`cancelled`).
- `reference` — optional provider reference string.
- `created_at` — timezone-aware timestamp.
- Indexes: `ix_payments_status` on status.

## refunds
- `id` — UUID primary key.
- `sale_id` — references `sales.id`, cascade delete.
- `amount` — numeric(12,2) refunded amount.
- `reason` — text reason, defaults to empty string.
- `created_by_user_id` — nullable reference to `users.id`, set null on delete.
- `created_at` — timezone-aware timestamp.

## cash_receipts
- `id` — UUID primary key.
- `sale_id` — references `sales.id`, cascade delete.
- `receipt_id` — provider receipt identifier, unique.
- `provider` — provider name.
- `payload_json` — JSON payload from provider.
- `created_at` — timezone-aware timestamp.

## cash_registers
- `id` — UUID primary key.
- `name` — unique register name.
- `type` — provider key (e.g., `mock`).
- `config` — JSONB configuration blob.
- `is_active` — boolean flag for activation.
- Indexes: `ix_cash_registers_active` on `is_active`.

## tenants
- `id` — UUID primary key.
- `name` — tenant display name.
- `code` — unique tenant code.
- `status` — enum(`active`,`inactive`), defaults to `active`.
- `created_at` — timezone-aware creation timestamp, defaults to `now()`.
- `updated_at` — timezone-aware update timestamp, defaults to `now()`.
- Indexes: `ix_tenants_status` on `status`, `ix_tenants_code` unique on `code`.

## modules (public)
- `id` — UUID primary key.
- `code` — unique module code.
- `name` — module name.
- `description` — optional module description.
- `is_active` — boolean flag, defaults to true.
- `created_at` — timezone-aware creation timestamp.
- Indexes: `uq_modules_code` unique on `code`.

## features (public)
- `id` — UUID primary key.
- `code` — unique feature code.
- `name` — feature name.
- `description` — optional feature description.
- `is_active` — boolean flag, defaults to true.
- `created_at` — timezone-aware creation timestamp.
- Indexes: `uq_features_code` unique on `code`.

## templates (public)
- `id` — UUID primary key.
- `name` — unique template name.
- `description` — optional template description.
- `module_codes` — JSON array of module code strings.
- `feature_codes` — JSON array of feature code strings.
- `created_at` — timezone-aware creation timestamp.
- Indexes: `uq_templates_name` unique on `name`.

## tenant_modules (tenant schema)
- `id` — UUID primary key.
- `module_id` — references `public.modules.id`, cascade delete.
- `is_enabled` — boolean flag, defaults to true.
- `created_at` — timezone-aware creation timestamp.
- Indexes: `ix_tenant_modules_module_id` on `module_id`, `uq_tenant_modules_module_id` unique on `module_id`.

## tenant_features (tenant schema)
- `id` — UUID primary key.
- `code` — feature code string.
- `is_enabled` — boolean flag, defaults to true.
- `created_at` — timezone-aware creation timestamp.
- Indexes: `ix_tenant_features_code` on `code`, `uq_tenant_features_code` unique on `code`.

## tenant_ui_prefs (tenant schema)
- `id` — UUID primary key.
- `prefs` — JSONB UI preference toggles.
- `created_at` — timezone-aware creation timestamp.
- `updated_at` — timezone-aware update timestamp.

All UUID defaults are generated in the application layer.
