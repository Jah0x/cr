# Environment variables

| Name | Purpose | Default |
| --- | --- | --- |
| `APP_ENV` | Deployment profile flag. | `dev` |
| `APP_HOST` | Host binding for uvicorn. | `0.0.0.0` |
| `APP_PORT` | Port binding for uvicorn. | `8000` |
| `DATABASE_URL` | Async SQLAlchemy URL using asyncpg, e.g. `postgresql+asyncpg://user:pass@host:5432/dbname`. | — |
| `JWT_SECRET` | Secret key for HS256 tokens. | — |
| `JWT_EXPIRES` | Access token lifetime in seconds. | `3600` |
| `CORS_ORIGINS` | Comma-separated allowed origins. | `*` |
| `COSTING_METHOD` | Stock costing configuration placeholder. | `LAST_PURCHASE` |
| `DISCOUNT_MAX_PERCENT_LINE` | Discount guardrail per line. | `0` |
| `DISCOUNT_MAX_PERCENT_RECEIPT` | Discount guardrail per receipt. | `0` |
| `DISCOUNT_MAX_AMOUNT_LINE` | Absolute discount guardrail per line. | `0` |
| `DISCOUNT_MAX_AMOUNT_RECEIPT` | Absolute discount guardrail per receipt. | `0` |
| `ALLOW_NEGATIVE_STOCK` | Allow selling below zero stock. | `False` |
| `FIRST_OWNER_EMAIL` | Bootstrap owner email used when no users exist. | — |
| `FIRST_OWNER_PASSWORD` | Bootstrap owner password used when no users exist. | — |
| `BOOTSTRAP_TOKEN` | Optional fallback token for platform admin APIs. | — |
| `CASH_REGISTER_PROVIDER` | Active cash register provider key (e.g., `mock`). | `mock` |
| `DEFAULT_CASH_REGISTER_ID` | Prefer a specific register ID when multiple are configured. | — |
| `ROOT_DOMAIN` | Root domain used to compose tenant URLs and resolve subdomains. | — |
| `PLATFORM_HOSTS` | Comma-separated hostnames treated as platform admin hosts. | — |
| `RESERVED_SUBDOMAINS` | Comma-separated tenant codes reserved for special routing. | — |
| `DEFAULT_TENANT_SLUG` | Default tenant slug used by the frontend. | — |
| `VITE_API_BASE_URL` | Frontend API base URL override. | `/api/v1` |
| `VITE_PLATFORM_HOSTS` | Frontend hostnames that should render the platform console. | — |

Legacy `OWNER_EMAIL` and `OWNER_PASSWORD` are accepted as aliases for `FIRST_OWNER_EMAIL` and `FIRST_OWNER_PASSWORD` to keep existing setups working.
