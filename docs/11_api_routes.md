# API routes (v1)

Base path: `/api/v1`

- Auth: JWT in `Authorization: Bearer <token>`
- Roles: `owner`, `manager`, `cashier`
- Unless stated otherwise, list endpoints are paginated and return `{ data: [...], meta: { page, per_page, total } }`.

## Health
- **GET /health** — public liveness probe. Response: `{ "status": "ok" }`.

## Auth
- **POST /auth/login** — anonymous. Payload: `{ "email": string, "password": string }`. Response: `{ "token": string, "user": { id, name, role } }`.
- **POST /auth/logout** — authenticated. Invalidates current token. Response: `{ "status": "ok" }`.
- **GET /auth/me** — authenticated. Returns `{ id, name, email, roles }` for the current user.

## User & role management (owner only)
- **GET /users** — list users with roles. Response items: `{ id, name, email, roles: ["owner"|"manager"|"cashier"], active }`.
- **POST /users** — create user. Payload: `{ "name": string, "email": string, "password": string, "roles": [...] , "active"?: boolean }`. Response: created user record.
- **PATCH /users/{id}** — update name/email/active status or reset password. Payload: `{ "name"?, "email"?, "password"?, "roles"?, "active"? }`. Response: updated user.
- **DELETE /users/{id}** — deactivate/remove a user account (soft delete recommended). Response: `{ "status": "ok" }`.

## Catalog
### Categories
- **GET /categories** — roles: owner/manager read-write, cashier read-only. Response items: `{ id, name, parent_id, active }`.
- **POST /categories** — owner/manager. Payload: `{ "name": string, "parent_id"?: uuid, "active"?: boolean }`. Response: created category.
- **PATCH /categories/{id}** — owner/manager. Payload: `{ "name"?, "parent_id"?, "active"? }`. Response: updated category.
- **DELETE /categories/{id}** — owner/manager. Response: `{ "status": "ok" }`.

### Brands
- **GET /brands** — owner/manager read-write, cashier read-only. Response items: `{ id, name, active }`.
- **POST /brands** — owner/manager. Payload: `{ "name": string, "active"?: boolean }`. Response: created brand.
- **PATCH /brands/{id}** — owner/manager. Payload: `{ "name"?, "active"? }`. Response: updated brand.
- **DELETE /brands/{id}** — owner/manager. Response: `{ "status": "ok" }`.

### Lines
- **GET /lines?brand_id=** — owner/manager read-write, cashier read-only. Response items: `{ id, name, brand_id, active }`.
- **POST /lines** — owner/manager. Payload: `{ "name": string, "brand_id": uuid, "active"?: boolean }`. Response: created line.
- **PATCH /lines/{id}** — owner/manager. Payload: `{ "name"?, "brand_id"?, "active"? }`. Response: updated line.
- **DELETE /lines/{id}** — owner/manager. Response: `{ "status": "ok" }`.

### Products
- **GET /products?category_id=&brand_id=&line_id=&q=&active=** — owner/manager read-write, cashier read-only. Response items: `{ id, name, sku, barcode, category_id, brand_id, line_id, price, active }`.
- **POST /products** — owner/manager. Payload: `{ "name": string, "sku"?: string, "barcode"?: string, "category_id"?: uuid, "brand_id"?: uuid, "line_id"?: uuid, "price": number, "active"?: boolean }`. Response: created product.
- **GET /products/{id}** — owner/manager/cashier. Response: full product detail `{ ...product, description?, image_url?, cost?, stock_on_hand? }`.
- **PATCH /products/{id}** — owner/manager. Payload: `{ "name"?, "sku"?, "barcode"?, "category_id"?, "brand_id"?, "line_id"?, "price"?, "active"? }`. Response: updated product.
- **DELETE /products/{id}** — owner/manager. Response: `{ "status": "ok" }`.

## Purchasing / Stock In
- **GET /suppliers** — owner/manager. Response items: `{ id, name, contact?, phone?, active }`.
- **POST /suppliers** — owner/manager. Payload: `{ "name": string, "contact"?: string, "phone"?: string, "active"?: boolean }`. Response: created supplier.
- **PATCH /suppliers/{id}** — owner/manager. Payload: `{ "name"?, "contact"?, "phone"?, "active"? }`. Response: updated supplier.
- **DELETE /suppliers/{id}** — owner/manager. Response: `{ "status": "ok" }`.

- **POST /purchase-invoices** — owner/manager create draft. Payload: `{ "supplier_id": uuid, "invoice_no"?: string, "invoice_date"?: date, "items"?: [{ "product_id": uuid, "qty": number, "cost": number }] }`. Response: draft invoice with `status: "DRAFT"` and totals.
- **GET /purchase-invoices?status=&from=&to=** — owner/manager. Filters by status/date. Response items include `{ id, supplier_id, status: "DRAFT"|"POSTED"|"VOID", total, invoice_date, created_at }`.
- **GET /purchase-invoices/{id}** — owner/manager. Response: full invoice with items and status.
- **POST /purchase-invoices/{id}/items** — owner/manager while DRAFT. Payload: `{ "items": [{ "product_id": uuid, "qty": number, "cost": number }] }`. Response: invoice with recalculated totals.
- **POST /purchase-invoices/{id}/post** — owner/manager. Action: posts draft, creates stock layers, marks `status: "POSTED"` and generates STOCK_IN moves. Response: posted invoice snapshot.
- **POST /purchase-invoices/{id}/void** — owner/manager. Action: voids draft; does not affect stock. Response: invoice with `status: "VOID"`.

## Stock
- **GET /stock?category_id=&brand_id=&line_id=&q=** — owner/manager read-write, cashier read-only (view only if allowed). Response items: `{ product_id, sku, name, on_hand, cost }`.
- **GET /stock/moves?product_id=&from=&to=** — owner/manager, cashier view-only when permitted. Response items: `{ id, product_id, type: "SALE_OUT"|"STOCK_IN"|"ADJUST"|"WRITE_OFF", qty, cost, created_at, ref }`.
- **POST /stock/adjustments** — owner/manager. Payload: `{ "type": "ADJUST"|"WRITE_OFF", "items": [{ "product_id": uuid, "qty": number, "reason"?: string }] }`. Response: `{ id, type, items, created_at }` and creates stock moves.

## POS Sales
- **POST /pos/sales** — cashier/manager/owner. Creates sale in `status: "OPEN"`. Payload: `{ "customer"?: string, "items"?: [{ "product_id": uuid, "qty": number, "price"?: number, "discount_pct"?: number, "discount_amount"?: number }] }`. Response: `{ id, status: "OPEN", totals, items }`.
- **GET /pos/sales/{id}** — cashier/manager/owner. Returns sale with items, payments, totals, status (`OPEN`|`FINALIZED`|`VOID`).
- **POST /pos/sales/{id}/items** — cashier/manager/owner while OPEN. Payload: `{ "items": [{ "product_id": uuid, "qty": number, "price"?: number, "discount_pct"?: number, "discount_amount"?: number }] }`. Response: sale with updated items/totals.
- **PATCH /pos/sales/{id}/items/{item_id}** — cashier/manager/owner while OPEN. Payload: `{ "qty"?, "price"?, "discount_pct"?, "discount_amount"? }`. Response: updated sale.
- **POST /pos/sales/{id}/payments** — cashier/manager/owner. Payload: `{ "method": "CASH"|"CARD"|"TRANSFER", "amount": number, "provider"?: string, "external_ref"?: string }`. Response: payment record `{ id, method, status: "INITIATED"|"SUCCESS"|"FAILED"|"CANCELED", amount, requires_confirmation }` and sale payment summary.
- **POST /pos/payments/{payment_id}/confirm** — manager/owner (or cashier when configured for CASH/CARD auto-success). Action: marks payment `SUCCESS`, updates sale paid totals. Response: payment with new status and linked sale summary.
- **POST /pos/payments/{payment_id}/cancel** — manager/owner. Action: marks payment `CANCELED` or `FAILED`, updates sale balance. Response: payment with new status.
- **POST /pos/sales/{id}/finalize** — cashier/manager/owner. Validates stock and discount limits; requires total payments >= total due and confirmations (TRANSFER confirmation requires manager/owner). Response: finalized sale `{ id, status: "FINALIZED", totals, paid, change_due, payments }` and creates `SALE_OUT` moves and COGS allocations.
- **POST /pos/sales/{id}/void** — manager/owner. Action: voids open/finalized sale (reverses stock and payments as needed). Response: sale with `status: "VOID"`.

## Reports
- **GET /reports/summary?from=&to=** — manager/owner. Response: `{ total_sales, total_items, avg_ticket, gross_profit, top_categories? }`.
- **GET /reports/by-category?from=&to=** — manager/owner. Response items: `{ category_id, name, sales, qty }`.
- **GET /reports/by-brand?from=&to=** — manager/owner. Response items: `{ brand_id, name, sales, qty }`.
- **GET /reports/top-products?from=&to=&limit=** — manager/owner. Response items: `{ product_id, name, sales, qty, margin }`.
- **GET /reports/stock-alerts?threshold=** — manager/owner. Response items: `{ product_id, name, on_hand, threshold }` for low-stock products.
- **GET /reports/revenue-by-payment?from=&to=** — manager/owner. Response items: `{ method: "CASH"|"CARD"|"TRANSFER", revenue, count }`.
- **GET /reports/unconfirmed-payments?from=&to=** — manager/owner. Lists pending transfers/manual card payments. Response items: `{ payment_id, sale_id, method, amount, status: "INITIATED", created_at, customer? }`.
