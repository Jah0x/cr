# Runbook

## Setup
1. Start PostgreSQL locally or with Docker: `docker compose up -d db` from repo root.
2. Populate environment variables from `docs/13_env_vars.md` (minimum: `DATABASE_URL`, `JWT_SECRET`, `FIRST_OWNER_EMAIL`, `FIRST_OWNER_PASSWORD`). For platform-only admin APIs set `BOOTSTRAP_TOKEN`.
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
- Readiness with DB check: `GET /readyz` or `/api/v1/health/ready`.
- Login: `POST /api/v1/auth/login` with owner credentials to obtain bearer token.
- Authenticated echo: `GET /api/v1/auth/me`.

## Platform admin
- Platform-only routes live under `/api/v1/platform` and require `Authorization: Bearer <BOOTSTRAP_TOKEN>`.
- Platform routes are additionally restricted to hosts in `PLATFORM_HOSTS`; align the frontend with `VITE_PLATFORM_HOSTS` so the UI renders the platform console on the same hostnames.
- Use platform endpoints to create tenants, modules, and templates, and to apply templates to tenants.
- Tenant module/feature toggles live under `/api/v1/tenant/settings` (owner-only) and are enforced across catalog, purchasing, stock, sales, POS, users, and reports.

## Operational notes
- Roles: owner manages users and cash registers; admin handles catalog, stock, purchasing; cashier handles sales.
- Stock moves are append-only; never delete historical records.
- Cash register provider defaults to `mock`; configure a different provider via env or database row without changing business logic.
- Tenancy: API dependencies resolve the tenant from the request host subdomain after excluding `PLATFORM_HOSTS` and `RESERVED_SUBDOMAINS`. The selected tenant id is placed on `request.state.tenant_id`. JWTs must include a tenant claim that matches the resolved tenant. Requests for inactive tenants return 403; missing or unknown tenants fail fast before handler logic runs.
