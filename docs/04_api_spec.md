# API spec (v1)

Base URL: /api/v1
Auth: JWT + role-based access control

## Health
GET /health -> { "status": "ok" }

## Catalog
GET/POST/PATCH/DELETE:
- /categories
- /brands
- /lines
- /products

GET /products?category_id=&brand_id=&line_id=&q=&active=

## Purchasing / Stock In
POST /purchase-invoices (create draft)
POST /purchase-invoices/{id}/items
POST /purchase-invoices/{id}/post
POST /purchase-invoices/{id}/void
GET  /purchase-invoices?status=&from=&to=

Rules:
- Only POSTED invoices affect stock and costing layers/batches.

## Stock
GET /stock?category_id=&brand_id=&line_id=&q=
GET /stock/moves?product_id=&from=&to=
POST /stock/adjustments  (ADJUST/WRITE_OFF; role-limited)

## POS Sales
POST /pos/sales (OPEN)
POST /pos/sales/{id}/items
PATCH /pos/sales/{id}/items/{item_id} (qty, price override if allowed, discounts)
POST /pos/sales/{id}/payments
POST /pos/sales/{id}/finalize
POST /pos/sales/{id}/void

### Payments
Payment methods: CASH | CARD | TRANSFER
Statuses: INITIATED | SUCCESS | FAILED | CANCELED

POST /pos/sales/{id}/payments
Payload:
{
  "method": "CASH|CARD|TRANSFER",
  "amount": 123.45,
  "provider": "optional",
  "external_ref": "optional"
}

POST /pos/payments/{payment_id}/confirm
POST /pos/payments/{payment_id}/cancel

Rules:
- CASH may be created as SUCCESS immediately (configurable).
- CARD may be manual: cashier enters external_ref and confirms (configurable).
- TRANSFER defaults to INITIATED and requires Manager/Owner confirmation.

Finalize rules:
- validate discount limits
- validate stock availability
- compute and store COGS by costing method
- create SALE_OUT moves
- mark PAID only when payments cover total_due and confirmations are satisfied

## Reports
GET /reports/summary?from=&to=
GET /reports/by-category?from=&to=
GET /reports/by-brand?from=&to=
GET /reports/top-products?from=&to=&limit=
GET /reports/stock-alerts?threshold=
GET /reports/revenue-by-payment?from=&to=
GET /reports/unconfirmed-payments?from=&to=
