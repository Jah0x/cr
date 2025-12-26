# Database schema (PostgreSQL)

## Conventions
- Primary keys: UUID generated with `gen_random_uuid()`
- Timestamps: `created_at` / `updated_at` use `timestamptz` with defaults to `now()`
- Monetary: `numeric(12,2)`
- Quantity: `numeric(12,3)`
- Boolean flags default to `false`
- All tables include `created_at`, `updated_at`, and `created_by` where relevant for auditing

## Tables

### users
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `email` text, not null, unique, lowercase
  - `password_hash` text, not null
  - `full_name` text, not null
  - `is_active` boolean not null default `true`
  - `last_login_at` timestamptz, nullable
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - unique on `email`
  - btree on `is_active`
- Constraints
  - PK on `id`
  - `email` must match simple email pattern via check if needed

### roles
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `code` text not null unique
  - `name` text not null
  - `description` text
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - unique on `code`
- Constraints
  - PK on `id`

### user_roles
- Columns
  - `user_id` UUID not null FK users(id)
  - `role_id` UUID not null FK roles(id)
  - `assigned_at` timestamptz not null default `now()`
- Indexes
  - unique composite on (`user_id`, `role_id`)
  - btree on `role_id`
- Constraints
  - PK composite (`user_id`, `role_id`)
  - FK `user_id` references users(id) on delete cascade
  - FK `role_id` references roles(id) on delete cascade

### categories
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `name` text not null
  - `slug` text not null unique
  - `parent_id` UUID FK categories(id), nullable
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - unique on `slug`
  - btree on `parent_id`
- Constraints
  - PK on `id`
  - FK `parent_id` references categories(id) on delete set null
  - check prevents parent_id = id

### brands
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `name` text not null unique
  - `slug` text not null unique
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - unique on `name`
  - unique on `slug`
- Constraints
  - PK on `id`

### product_lines
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `brand_id` UUID not null FK brands(id)
  - `name` text not null
  - `slug` text not null unique
  - `description` text
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - unique on `slug`
  - btree on `brand_id`
- Constraints
  - PK on `id`
  - FK `brand_id` references brands(id) on delete cascade

### products
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `product_line_id` UUID nullable FK product_lines(id)
  - `category_id` UUID nullable FK categories(id)
  - `sku` text not null unique
  - `name` text not null
  - `barcode` text unique
  - `description` text
  - `unit` text not null default 'pcs'
  - `is_active` boolean not null default true
  - `reorder_level` numeric(12,3) default 0
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - unique on `sku`
  - unique on `barcode` where barcode is not null
  - btree on `category_id`
  - btree on `product_line_id`
- Constraints
  - PK on `id`
  - FK `product_line_id` references product_lines(id) on delete set null
  - FK `category_id` references categories(id) on delete set null

### suppliers
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `name` text not null
  - `contact_email` text
  - `phone` text
  - `tax_id` text
  - `currency` char(3) not null default 'USD'
  - `address` text
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - unique on (`name`, `tax_id`) where tax_id is not null
  - btree on `name`
- Constraints
  - PK on `id`

### purchase_invoices
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `supplier_id` UUID not null FK suppliers(id)
  - `invoice_no` text not null
  - `invoice_date` date not null
  - `currency` char(3) not null default 'USD'
  - `exchange_rate` numeric(12,6) not null default 1.0 (to home currency)
  - `status` text not null default 'draft' check in ('draft','approved','cancelled','paid')
  - `subtotal` numeric(12,2) not null default 0
  - `tax` numeric(12,2) not null default 0
  - `total` numeric(12,2) generated always as (subtotal + tax) stored
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - unique on (`supplier_id`, `invoice_no`)
  - btree on `invoice_date`
  - btree on `status`
- Constraints
  - PK on `id`
  - FK `supplier_id` references suppliers(id)

### purchase_items
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `invoice_id` UUID not null FK purchase_invoices(id)
  - `product_id` UUID not null FK products(id)
  - `quantity` numeric(12,3) not null
  - `unit_price` numeric(12,2) not null
  - `discount` numeric(12,2) not null default 0
  - `tax` numeric(12,2) not null default 0
  - `line_total` numeric(12,2) generated always as ((quantity * unit_price) - discount + tax) stored
  - `expected_receipt_date` date
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - btree on `invoice_id`
  - btree on `product_id`
- Constraints
  - PK on `id`
  - FK `invoice_id` references purchase_invoices(id) on delete cascade
  - FK `product_id` references products(id)
  - check quantity > 0 and unit_price >= 0

### stock_batches
- Purpose: lots received via purchases or adjustments, used for FIFO costing.
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `product_id` UUID not null FK products(id)
  - `source_purchase_item_id` UUID nullable FK purchase_items(id)
  - `quantity_received` numeric(12,3) not null
  - `quantity_remaining` numeric(12,3) not null
  - `unit_cost` numeric(12,4) not null (in home currency)
  - `received_at` timestamptz not null default `now()`
  - `expiry_date` date
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - btree on `product_id`
  - btree on `received_at`
  - btree on `expiry_date`
- Constraints
  - PK on `id`
  - FK `product_id` references products(id)
  - FK `source_purchase_item_id` references purchase_items(id) on delete set null
  - check `quantity_remaining` between 0 and `quantity_received`

### stock_moves
- Purpose: inventory movements increasing or decreasing on-hand and batches.
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `product_id` UUID not null FK products(id)
  - `batch_id` UUID nullable FK stock_batches(id) (for issues referencing FIFO batch)
  - `source_type` text not null check in ('purchase_receipt','sale_issue','adjustment','transfer_in','transfer_out')
  - `source_id` UUID nullable (links to purchase_items.id, sale_items.id, or adjustment doc)
  - `quantity` numeric(12,3) not null (positive for increase, negative for decrease)
  - `unit_cost` numeric(12,4) not null default 0 (home currency at move time)
  - `moved_at` timestamptz not null default `now()`
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - btree on `product_id`
  - btree on `batch_id`
  - btree on (`source_type`, `source_id`)
  - btree on `moved_at`
- Constraints
  - PK on `id`
  - FK `product_id` references products(id)
  - FK `batch_id` references stock_batches(id) on delete set null
  - check quantity <> 0

### sales
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `customer_name` text not null
  - `sale_date` date not null
  - `status` text not null default 'draft' check in ('draft','confirmed','cancelled','paid')
  - `currency` char(3) not null default 'USD'
  - `exchange_rate` numeric(12,6) not null default 1.0
  - `subtotal` numeric(12,2) not null default 0
  - `tax` numeric(12,2) not null default 0
  - `total` numeric(12,2) generated always as (subtotal + tax) stored
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - btree on `sale_date`
  - btree on `status`
- Constraints
  - PK on `id`

### sale_items
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `sale_id` UUID not null FK sales(id)
  - `product_id` UUID not null FK products(id)
  - `quantity` numeric(12,3) not null
  - `unit_price` numeric(12,2) not null
  - `discount` numeric(12,2) not null default 0
  - `tax` numeric(12,2) not null default 0
  - `line_total` numeric(12,2) generated always as ((quantity * unit_price) - discount + tax) stored
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - btree on `sale_id`
  - btree on `product_id`
- Constraints
  - PK on `id`
  - FK `sale_id` references sales(id) on delete cascade
  - FK `product_id` references products(id)
  - check quantity > 0 and unit_price >= 0

### sale_item_cost_allocations (FIFO)
- Purpose: links sale items to stock batches to record cost of goods sold using FIFO.
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `sale_item_id` UUID not null FK sale_items(id)
  - `batch_id` UUID not null FK stock_batches(id)
  - `quantity` numeric(12,3) not null
  - `unit_cost` numeric(12,4) not null (copied from batch at allocation time)
  - `allocated_at` timestamptz not null default `now()`
- Indexes
  - unique on (`sale_item_id`, `batch_id`)
  - btree on `batch_id`
- Constraints
  - PK on `id`
  - FK `sale_item_id` references sale_items(id) on delete cascade
  - FK `batch_id` references stock_batches(id)
  - check quantity > 0

### payments
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `sale_id` UUID nullable FK sales(id)
  - `purchase_invoice_id` UUID nullable FK purchase_invoices(id)
  - `method` text not null check in ('cash','card','bank_transfer','mobile')
  - `amount` numeric(12,2) not null
  - `currency` char(3) not null default 'USD'
  - `paid_at` timestamptz not null default `now()`
  - `reference` text
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - btree on `sale_id`
  - btree on `purchase_invoice_id`
  - btree on `paid_at`
- Constraints
  - PK on `id`
  - FK `sale_id` references sales(id) on delete set null
  - FK `purchase_invoice_id` references purchase_invoices(id) on delete set null
  - check exactly one of sale_id or purchase_invoice_id is not null

### cost_allocations_summary (periodic cost tracking)
- Columns
  - `id` UUID PK default `gen_random_uuid()`
  - `period` date not null (first day of month)
  - `product_id` UUID not null FK products(id)
  - `opening_qty` numeric(12,3) not null default 0
  - `opening_cost` numeric(12,2) not null default 0
  - `purchased_qty` numeric(12,3) not null default 0
  - `purchased_cost` numeric(12,2) not null default 0
  - `sold_qty` numeric(12,3) not null default 0
  - `cogs` numeric(12,2) not null default 0
  - `closing_qty` numeric(12,3) not null default 0
  - `closing_cost` numeric(12,2) not null default 0
  - `created_at` timestamptz not null default `now()`
  - `updated_at` timestamptz not null default `now()`
- Indexes
  - unique on (`period`, `product_id`)
  - btree on `product_id`
- Constraints
  - PK on `id`
  - FK `product_id` references products(id)

## Views (optional)
- `v_stock_on_hand`: aggregates stock_moves by product (and batch) to compute quantity on hand and weighted average cost per product; should filter out cancelled docs if status exists.
- `v_sales_summary`: aggregates sales and sale_items per day/month with gross revenue, tax, discounts, and cost of goods sold via sale_item_cost_allocations.
