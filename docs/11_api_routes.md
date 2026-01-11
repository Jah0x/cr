# API routes (v1)

Base path: `/api/v1`

## Health
- **GET /health** — public liveness probe.
- **GET /health/z** — public liveness probe alias.
- **GET /health/ready** — readiness probe hitting the database; accepts an optional tenant hint via `X-Tenant-ID`, `X-Tenant-Code`/`X-Tenant`, or `tenant` query. When a tenant is provided it validates the tenant is active and migrations are applied for that schema before returning `{ "status": "ready" }`; without a tenant it only checks base connectivity.
- **GET /healthz** — root liveness alias.
- **GET /readyz** — root readiness alias with DB check.

## Auth
- **POST /auth/login** — anonymous. Payload: `{ "email": string, "password": string }`. Response: `{ "access_token": string, "token_type": "bearer" }`.
- **GET /auth/me** — bearer token required. Response: `{ "id": uuid, "email": string, "is_active": bool, "roles": [ { "id": uuid, "name": string } ] }`.

Notes: registration is not public; owners provision accounts.

## Users (owner)
- Access: `owner` only.
- **GET /users** — list users with roles.
- **POST /users** — create user. Payload: `{ "email": string, "password": string, "roles": ["owner"|"admin"|"cashier"] }`. Response mirrors list item.
- **POST /users/{user_id}/roles** — replace roles. Payload: `{ "roles": ["owner"|"admin"|"cashier"] }`.

## Catalog (owner, admin)
### Categories
- **GET /categories** — list.
- **POST /categories** — create. Payload: `{ "name": string, "is_active": bool }`.
- **PATCH /categories/{category_id}** — update name/activation. Payload: `{ "name"?: string, "is_active"?: bool }`.
- **DELETE /categories/{category_id}** — delete.

### Brands
- **GET /brands** — list.
- **POST /brands** — create. Payload: `{ "name": string, "is_active": bool }`.
- **PATCH /brands/{brand_id}** — update. Payload: `{ "name"?: string, "is_active"?: bool }`.
- **DELETE /brands/{brand_id}** — delete.

### Product lines
- **GET /lines?brand_id=** — list or filter.
- **POST /lines** — create. Payload: `{ "name": string, "brand_id": uuid, "is_active": bool }`.
- **PATCH /lines/{line_id}** — update. Payload: `{ "name"?: string, "brand_id"?: uuid, "is_active"?: bool }`.
- **DELETE /lines/{line_id}** — delete.

### Products
- **GET /products** with filters `category_id`, `brand_id`, `line_id`, `q`, `is_active`.
- **POST /products** — create. Payload: `{ "sku": string, "name": string, "description"?: string, "image_url"?: string, "category_id"?: uuid, "brand_id"?: uuid, "line_id"?: uuid, "price": decimal, "is_active": bool }`.
- **GET /products/{product_id}** — fetch single.
- **PATCH /products/{product_id}** — update fields from create payload.
- **DELETE /products/{product_id}** — soft delete (sets `is_active=false`).

## Purchasing (owner, admin)
### Suppliers
- **GET /suppliers** — list.
- **POST /suppliers** — create. Payload: `{ "name": string, "contact": string }`.
- **PATCH /suppliers/{supplier_id}** — update. Payload: `{ "name"?: string, "contact"?: string }`.
- **DELETE /suppliers/{supplier_id}** — delete.

### Purchase invoices
- **POST /purchase-invoices** — create draft. Payload: `{ "supplier_id"?: uuid }`.
- **GET /purchase-invoices?status=** — list by optional status (`draft|posted|void`).
- **GET /purchase-invoices/{invoice_id}** — fetch invoice with items.
- **POST /purchase-invoices/{invoice_id}/items** — add line to draft. Payload: `{ "product_id": uuid, "quantity": decimal, "unit_cost": decimal }`.
- **POST /purchase-invoices/{invoice_id}/post** — post draft, creates stock moves/batches. Errors on empty invoices.
- **POST /purchase-invoices/{invoice_id}/void** — void invoice.

## Stock (owner, admin)
- **GET /stock** — aggregate on-hand by product.
- **GET /stock/moves?product_id=** — list stock moves (append-only history).
- **POST /stock/adjustments** — manual adjustment or write-off. Payload: `{ "product_id": uuid, "quantity": decimal, "reason": string }`.

## Sales (owner, cashier)
- **POST /sales** — create sale transaction. Payload: `{ "items": [ { "product_id": uuid, "qty": decimal, "unit_price"?: decimal } ], "currency"?: string, "payments"?: [ { "amount": decimal, "method": "cash"|"card"|"external", "currency"?: string, "status"?: "pending"|"confirmed"|"cancelled", "reference"?: string } ], "cash_register_id"?: uuid }`. Atomically writes sale, payments, stock moves, and mock receipt.
- **GET /sales?status=&date_from=&date_to=** — list sales.
- **GET /sales/{sale_id}** — sale detail with items, receipts, payments, refunds.
- **POST /sales/{sale_id}/void** — owner only. Marks sale void and restocks items.
- **POST /sales/{sale_id}/refunds** — create refund (partial or full). Payload: `{ "amount"?: decimal, "reason"?: string, "items"?: [ { "sale_item_id": uuid, "qty": decimal } ] }`. Restocks returned quantities and records refund plus cash register entry.

## Cash registers (owner)
- Bootstraps one active mock register if none exist. Future endpoints will manage registers; current provider selection uses `CASH_REGISTER_PROVIDER` or the active DB record.

## Platform (bootstrap token, platform host only)
Auth: `Authorization: Bearer <BOOTSTRAP_TOKEN>`.

### Tenants
- **GET /platform/tenants** — list tenants.
- **POST /platform/tenants** — create tenant. Payload: `{ "name": string, "code": string, "template_id"?: uuid, "owner_email": string, "owner_password": string }`. Response: `{ "id": uuid, "name": string, "code": string, "status": "active"|"inactive", "tenant_url": string, "owner_email": string, "owner_password": string }`.
- **POST /platform/tenants/{tenant_id}/apply-template** — apply template. Payload: `{ "template_id": uuid }`.

### Modules
- **GET /platform/modules** — list modules.
- **POST /platform/modules** — create module. Payload: `{ "code": string, "name": string, "description"?: string, "is_active": bool }`.

### Templates
- **GET /platform/templates** — list templates.
- **POST /platform/templates** — create template. Payload: `{ "name": string, "description"?: string, "module_codes": string[], "feature_codes": string[] }`.
