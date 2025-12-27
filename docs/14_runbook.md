# Runbook

## Setup
1. Start PostgreSQL locally or with Docker: `docker compose up -d db` from repo root.
2. Populate environment variables from `docs/13_env_vars.md` (minimum: `DATABASE_URL`, `JWT_SECRET`, `FIRST_OWNER_EMAIL`, `FIRST_OWNER_PASSWORD`).
3. Install backend dependencies: `cd backend && poetry install`.
4. Apply migrations: `cd backend && poetry run alembic upgrade head`.
5. Launch API: `cd backend && poetry run uvicorn app.main:app --host $APP_HOST --port $APP_PORT`.

Bootstrap creates the first owner and all roles automatically on startup if the users table is empty and `FIRST_OWNER_EMAIL`/`FIRST_OWNER_PASSWORD` are set. A default mock cash register is seeded when none exist.

## Database operations
- Generate migration after model changes: `cd backend && poetry run alembic revision --autogenerate -m "message"`.
- Apply migrations: `cd backend && poetry run alembic upgrade head`.
- Inspect current revision: `cd backend && poetry run alembic current`.

## Running and health
- Liveness: `GET /healthz` or `/api/v1/health`.
- Readiness with DB check: `GET /readyz` or `/api/v1/health/ready`; supply `X-Tenant-ID`, `X-Tenant-Code`/`X-Tenant`, or `tenant` query to verify readiness for a specific tenant schema and migrations.
- Login: `POST /api/v1/auth/login` with owner credentials to obtain bearer token.
- Authenticated echo: `GET /api/v1/auth/me`.

## Operational notes
- Roles: owner manages users and cash registers; admin handles catalog, stock, purchasing; cashier handles sales.
- Stock moves are append-only; never delete historical records.
- Cash register provider defaults to `mock`; configure a different provider via env or database row without changing business logic.
- Tenancy: API dependencies resolve the tenant in order of `X-Tenant-ID` (UUID), `X-Tenant-Code`/`X-Tenant` (string), JWT `tenant_id`, then request host subdomain. The selected tenant id is placed on `request.state.tenant_id`. JWTs must include a tenant claim that matches the resolved tenant. Requests for inactive tenants return 403; missing or unknown tenants fail fast before handler logic runs.
