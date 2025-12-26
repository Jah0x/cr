# Database schema

Alembic revisions:
- `0001_initial` — authentication tables.
- `0002_catalog` — catalog tables and seeded roles.

## users
- `id` — UUID primary key.
- `email` — unique email address.
- `password_hash` — bcrypt hash.
- `is_active` — boolean flag for login eligibility.

## roles
- `id` — UUID primary key.
- `name` — unique role name. Seeds cover `owner`, `manager`, `cashier` (ON CONFLICT DO NOTHING to avoid duplicates).

## user_roles
- `user_id` — references `users.id`, cascade delete.
- `role_id` — references `roles.id`, cascade delete.

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
- `description` — free text description.
- `image_url` — optional image link.
- `category_id` — nullable reference to `categories.id`, set null on delete.
- `brand_id` — nullable reference to `brands.id`, set null on delete.
- `line_id` — nullable reference to `product_lines.id`, set null on delete.
- `price` — numeric(12,2) price.
- `is_active` — soft-delete/activation flag.

All UUID defaults are generated in the application layer.
