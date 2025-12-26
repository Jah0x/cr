# Environment variables

## Backend
| Variable | Default | Description |
| --- | --- | --- |
| DATABASE_URL | (required) | PostgreSQL DSN using `postgresql+asyncpg://` scheme. |
| APP_ENV | dev | Runtime mode: `dev` enables debug-friendly defaults, `prod` locks down CORS and cookies. |
| APP_HOST | 0.0.0.0 | Host binding for FastAPI. |
| APP_PORT | 8000 | Port binding for FastAPI. |
| CORS_ORIGINS | * | Comma-separated origins allowed by CORS. Set to explicit origins in `prod`. |
| COSTING_METHOD | LAST_PURCHASE | Inventory costing strategy: `LAST_PURCHASE`, `WEIGHTED_AVERAGE`, or `FIFO`. |
| DISCOUNT_MAX_PERCENT_LINE | 0 | Maximum percent discount per line item. |
| DISCOUNT_MAX_PERCENT_RECEIPT | 0 | Maximum percent discount on total receipt. |
| DISCOUNT_MAX_AMOUNT_LINE | 0 | Maximum absolute discount per line item. |
| DISCOUNT_MAX_AMOUNT_RECEIPT | 0 | Maximum absolute discount on total receipt. |
| ALLOW_NEGATIVE_STOCK | false | Allow sales to proceed when on-hand stock would drop below zero. |

### Auth and session
| Variable | Default | Description |
| --- | --- | --- |
| JWT_SECRET | (required) | Symmetric secret for signing access tokens. |
| JWT_ACCESS_TTL_SECONDS | 3600 | Access token lifetime in seconds. |
| JWT_REFRESH_TTL_SECONDS | 86400 | Refresh token lifetime in seconds (set to `0` to disable refresh flow). |

### Bootstrap owner account
| Variable | Default | Description |
| --- | --- | --- |
| OWNER_NAME | Owner | Display name for the initial owner. |
| OWNER_EMAIL | owner@example.com | Email used to seed the first owner account. |
| OWNER_PASSWORD | change-me | Password used to seed the first owner account; rotate immediately in production. |

### Payments and terminal integration
| Variable | Default | Description |
| --- | --- | --- |
| PAYMENT_PROVIDER | MANUAL | Payment adapter: `MANUAL` (in-app confirmation) or `TERMINAL` (external terminal; see EPIC phase 7). |
| PAYMENT_CASH_AUTO_SUCCESS | true | When `true`, CASH payments are recorded as `SUCCESS` immediately. |
| PAYMENT_CARD_REQUIRES_CONFIRMATION | true | When `true`, CARD payments stay `INITIATED` until confirmed by manager/owner. |
| PAYMENT_TRANSFER_REQUIRES_CONFIRMATION | true | When `true`, TRANSFER payments require manager/owner confirmation. |

### Feature flags
| Variable | Default | Description |
| --- | --- | --- |
| FEATURE_ENABLE_REPORTS | true | Toggle report endpoints and UI modules. |
| FEATURE_ENABLE_POS | true | Toggle POS flows (sales, payments, finalize). |
| FEATURE_ENABLE_REFRESH_TOKENS | true | Enables refresh token issuance and validation in addition to access tokens. |

## Frontend
| Variable | Default | Description |
| --- | --- | --- |
| VITE_API_BASE_URL | http://localhost:8000/api/v1 | Base API URL for axios client (use `NEXT_PUBLIC_API_BASE_URL` when using Next.js). |
| VITE_PAYMENT_PROVIDER | MANUAL | Mirrors backend `PAYMENT_PROVIDER` to surface terminal prompts or manual confirmation UX. |
| VITE_FEATURE_ENABLE_REPORTS | true | Feature toggle for reports menus and data fetching. |
| VITE_FEATURE_ENABLE_POS | true | Feature toggle for POS surface; hide tiles/cart when `false`. |
