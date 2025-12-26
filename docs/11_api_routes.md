# API routes (v1)

Base path: `/api/v1`

## Health
- **GET /health** — public liveness probe. Response: `{ "status": "ok" }`.

## Auth
- **POST /auth/login** — anonymous. Payload: `{ "email": string, "password": string }`. Response: `{ "access_token": string, "token_type": "bearer" }`.
- **GET /auth/me** — requires `Authorization: Bearer <access_token>`. Response: `{ "id": uuid, "email": string }`.

Notes:
- There is no public registration endpoint. Accounts are provisioned through migrations or CLI tasks.

## Catalog
- Access control: `owner` and `manager` roles only. Requests from a `cashier` role return HTTP 403.

### Categories
- **GET /categories** — lists categories. Response: `[ { "id": uuid, "name": string, "is_active": bool } ]`.
- **POST /categories** — create. Payload: `{ "name": string, "is_active": bool }`. Response mirrors GET item.
- **PATCH /categories/{category_id}** — update name/activation. Payload: `{ "name"?: string, "is_active"?: bool }`. Response mirrors GET item.
- **DELETE /categories/{category_id}** — hard delete. Response: `{ "detail": "deleted" }`.

### Brands
- **GET /brands** — lists brands. Response: `[ { "id": uuid, "name": string, "is_active": bool } ]`.
- **POST /brands** — create. Payload: `{ "name": string, "is_active": bool }`. Response mirrors GET item.
- **PATCH /brands/{brand_id}** — update name/activation. Payload: `{ "name"?: string, "is_active"?: bool }`. Response mirrors GET item.
- **DELETE /brands/{brand_id}** — hard delete. Response: `{ "detail": "deleted" }`.

### Product lines
- **GET /lines?brand_id=** — list all lines or filter by brand. Response: `[ { "id": uuid, "name": string, "brand_id": uuid, "is_active": bool } ]`.
- **POST /lines** — create. Payload: `{ "name": string, "brand_id": uuid, "is_active": bool }`. Response mirrors GET item.
- **PATCH /lines/{line_id}** — update name/brand/activation. Payload: `{ "name"?: string, "brand_id"?: uuid, "is_active"?: bool }`. Response mirrors GET item.
- **DELETE /lines/{line_id}** — hard delete. Response: `{ "detail": "deleted" }`.

### Products
- **GET /products?category_id=&brand_id=&line_id=&q=&is_active=** — list products with optional filters. `is_active` defaults to `true` to hide soft-deleted items. Response: `[ { "id": uuid, "sku": string, "name": string, "description": string, "image_url": string|null, "category_id": uuid|null, "brand_id": uuid|null, "line_id": uuid|null, "price": decimal, "is_active": bool } ]`.
- **POST /products** — create. Payload: `{ "sku": string, "name": string, "description": string, "image_url"?: string, "category_id"?: uuid, "brand_id"?: uuid, "line_id"?: uuid, "price": decimal, "is_active": bool }`. Response mirrors GET item.
- **GET /products/{product_id}** — fetch single product. Response mirrors GET item.
- **PATCH /products/{product_id}** — update fields. Payload: `{ "sku"?: string, "name"?: string, "description"?: string, "image_url"?: string, "category_id"?: uuid, "brand_id"?: uuid, "line_id"?: uuid, "price"?: decimal, "is_active"?: bool }`. Response mirrors GET item.
- **DELETE /products/{product_id}** — soft delete. Action flips `is_active` to `false` and returns `{ "detail": "deleted" }`.
