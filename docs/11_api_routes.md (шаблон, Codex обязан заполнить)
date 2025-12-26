# API routes (v1)

Base: /api/v1

## Auth
- POST /auth/login
- POST /auth/logout
- GET /auth/me

## Catalog
### Categories
- GET /categories
- POST /categories
- PATCH /categories/{id}
- DELETE /categories/{id}

### Brands
- GET /brands
- POST /brands
- PATCH /brands/{id}
- DELETE /brands/{id}

### Lines
- GET /lines?brand_id=
- POST /lines
- PATCH /lines/{id}
- DELETE /lines/{id}

### Products
- GET /products?category_id=&brand_id=&line_id=&q=&active=
- POST /products
- GET /products/{id}
- PATCH /products/{id}
- DELETE /products/{id}

## Purchasing
- GET /suppliers
- POST /suppliers
- PATCH /suppliers/{id}
- DELETE /suppliers/{id}

- POST /purchase-invoices
- GET /purchase-invoices?status=&from=&to=
- GET /purchase-invoices/{id}
- POST /purchase-invoices/{id}/items
- POST /purchase-invoices/{id}/post
- POST /purchase-invoices/{id}/void

## Stock
- GET /stock?filters...
- GET /stock/moves?product_id=&from=&to=
- POST /stock/adjustments

## POS
- POST /pos/sales
- GET /pos/sales/{id}
- POST /pos/sales/{id}/items
- PATCH /pos/sales/{id}/items/{item_id}
- POST /pos/sales/{id}/payments
- POST /pos/sales/{id}/finalize
- POST /pos/sales/{id}/void

## Reports
- GET /reports/summary?from=&to=
- GET /reports/by-category?from=&to=
- GET /reports/by-brand?from=&to=
- GET /reports/top-products?from=&to=&limit=
- GET /reports/stock-alerts?threshold=
