# Codex Task: start implementation

Read docs/ and follow CODEx_RULES.md strictly.

## Stack (must follow)
Backend:
- Python 3.12, FastAPI, SQLAlchemy 2 async (asyncpg), Alembic, Pydantic v2
- JWT auth + RBAC (Owner/Manager/Cashier)
- ruff + black, pytest smoke tests

Frontend:
- TypeScript, React + Vite
- react-router
- TanStack Query
- eslint + prettier

## Core features
- Catalog: categories tree, brands, lines, products with image_url
- Purchasing: suppliers, purchase invoices (draft->post->void), items
- Stock: on-hand, moves, adjustments/write-offs (role-limited)
- POS: tile-based selection + search, cart, discounts (% or amount), payments
- Payments: CASH/CARD/TRANSFER + statuses + confirm/cancel endpoints
- Costing methods: LAST_PURCHASE, WEIGHTED_AVERAGE, FIFO (with allocations)
- Reports: summary + slices + payment breakdown + unconfirmed payments list

## Documentation (mandatory updates)
- docs/11_api_routes.md: full routes with payload/response + roles
- docs/12_db_schema.md: full schema docs
- docs/13_env_vars.md: full env list
- docs/14_runbook.md: how to run, migrate, seed, troubleshoot
- docs/15_decisions.md: decisions log

## Done criteria
- clean DB migrate from scratch
- admin can create catalog and post purchase invoice
- POS can sell with discounts and mixed payment methods
- cannot finalize sale without enough confirmed payments
- reports show turnover/cogs/profit and payment breakdown
