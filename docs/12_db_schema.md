# Database schema

Alembic revisions:
- `0001_initial` — authentication tables with seeded roles.
- `0002_catalog` — catalog tables.
- `0003_purchasing_stock` — purchasing and stock tables.

## users
- `id` — UUID primary key.
- `email` — unique email address.
- `password_hash` — bcrypt hash.
- `is_active` — boolean flag for login eligibility, defaults to true.
- `created_at` — timezone-aware creation timestamp, defaults to `now()`.
- Indexes: `ix_users_email` unique index on `email`.

## roles
- `id` — UUID primary key.
- `name` — unique role name.
- Seeded values: `owner`, `manager`, `cashier`.
- Indexes: `ix_roles_name` unique index on `name`.

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
- `quantity` — numeric(12,3) delta (positive for inbound, negative for outbound).
- `reason` — reason label such as `PURCHASE_IN` or `sale`.
- `reference` — free-form reference string, defaults to empty string.
- `created_at` — timezone-aware creation timestamp, defaults to `now()`.

## stock_batches
- `id` — UUID primary key.
- `product_id` — references `products.id`, cascade delete.
- `quantity` — numeric(12,3) remaining quantity in batch.
- `unit_cost` — numeric(12,2) unit cost for batch.
- `purchase_item_id` — nullable reference to `purchase_items.id`, set null on delete.

All UUID defaults are generated in the application layer.
