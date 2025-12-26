# Environment variables

| Name | Purpose | Default |
| --- | --- | --- |
| `APP_ENV` | Deployment profile flag. | `dev` |
| `APP_HOST` | Host binding for uvicorn. | `0.0.0.0` |
| `APP_PORT` | Port binding for uvicorn. | `8000` |
| `DATABASE_URL` | Async SQLAlchemy URL using asyncpg, e.g. `postgresql+asyncpg://user:pass@host:5432/dbname`. | — |
| `JWT_SECRET` | Secret key for HS256 tokens. | — |
| `JWT_ACCESS_TTL_SECONDS` | Access token lifetime in seconds. | `3600` |
| `JWT_REFRESH_TTL_SECONDS` | Refresh token lifetime in seconds (reserved). | `86400` |
| `CORS_ORIGINS` | Comma-separated allowed origins. | `*` |
| `FIRST_OWNER_EMAIL` | Email for bootstrap owner account. | — |
| `FIRST_OWNER_PASSWORD` | Password for bootstrap owner account. | — |
| `COSTING_METHOD` | Placeholder for future stock costing configuration. | `LAST_PURCHASE` |
| `DISCOUNT_MAX_PERCENT_LINE` | Placeholder discount guardrail. | `0` |
| `DISCOUNT_MAX_PERCENT_RECEIPT` | Placeholder discount guardrail. | `0` |
| `DISCOUNT_MAX_AMOUNT_LINE` | Placeholder discount guardrail. | `0` |
| `DISCOUNT_MAX_AMOUNT_RECEIPT` | Placeholder discount guardrail. | `0` |
| `ALLOW_NEGATIVE_STOCK` | Placeholder flag for stock validation. | `False` |
