# Runbook

## Setup
1. Provision PostgreSQL (local, managed service, or Kubernetes). Capture its connection URL.
2. Populate environment variables (required: `DATABASE_URL`, `JWT_SECRET`, `ROOT_DOMAIN`, `PLATFORM_HOSTS`, `RESERVED_SUBDOMAINS`, `FIRST_OWNER_EMAIL`, `FIRST_OWNER_PASSWORD`; optional: `BOOTSTRAP_TOKEN`).
3. Install backend dependencies: `cd backend && poetry install`.
4. Apply migrations (public + tenant): `cd backend && poetry run python -m app.cli migrate-all`.
5. Launch API: `cd backend && poetry run uvicorn app.main:app --host $APP_HOST --port $APP_PORT`.

## Kubernetes run (conceptual)
1. Build and publish backend/frontend container images.
2. Create Deployments for backend and frontend, Services for each, and an Ingress (or Gateway) for routing.
3. Provide all required environment variables to the backend Deployment.
4. Run migrations as a one-off Job or `kubectl exec` with `python -m app.cli migrate-all`.
5. Roll out the Deployments and verify health endpoints.

## Database operations
- Generate migration after model changes: `cd backend && poetry run alembic revision --autogenerate -m "message"`.
- Apply public migrations only: `cd backend && poetry run alembic upgrade head` (useful for schema-only changes).
- Apply public + tenant migrations: `cd backend && poetry run python -m app.cli migrate-all`.
- Inspect current revision: `cd backend && poetry run alembic current`.
- Check where the `cashiershiftstatus` type exists:
  ```sql
  SELECT n.nspname, t.typname
  FROM pg_type t
  JOIN pg_namespace n ON t.typnamespace = n.oid
  WHERE t.typname = 'cashiershiftstatus';
  ```

## Troubleshooting migrations
- Verify migration idempotency in a controlled environment:
  1. Run migrations on an empty tenant schema.
  2. Run migrations a second time without any changes and confirm there are no errors.
  3. Repeat the scenario with `cashiershiftstatus` already existing in `public`, and confirm tenant migrations still complete successfully.
- Production recovery notes:
  - First, check the type location with the SQL query above.
  - If a migration failed after partial execution, prefer shipping a fixed migration and rerunning rather than manual catalog edits.
  - Do not manually drop types until dependency analysis confirms it is safe.

## Running and health
- Liveness: `GET /healthz` or `/api/v1/health`.
- Readiness with DB check: `GET /readyz` or `/api/v1/health/ready`.
- Login: `POST /api/v1/auth/login` with owner credentials to obtain bearer token.
- Authenticated echo: `GET /api/v1/auth/me`.

## Platform admin
- Platform-only routes live under `/api/v1/platform` and require `Authorization: Bearer <platform JWT>` (fallback: `BOOTSTRAP_TOKEN`).
- Platform JWTs are issued by `POST /api/v1/platform/auth/login` using the configured `FIRST_OWNER_EMAIL`/`FIRST_OWNER_PASSWORD`.
- Platform routes are additionally restricted to hosts in `PLATFORM_HOSTS`; align the frontend with `VITE_PLATFORM_HOSTS` so the UI renders the platform console on the same hostnames.
- Use platform endpoints to create tenants, modules, and templates, and to apply templates to tenants.
- Tenant module/feature toggles live under `/api/v1/tenant/settings` (owner-only) and are enforced across catalog, purchasing, stock, sales, POS, users, and reports. Missing tenant overrides are treated as disabled until explicitly enabled.

## Troubleshooting auth regressions
- Verify access logs from the backend include `/api/v1/auth/login` start/end and the final response code.
- If `/api/v1/auth/login` returns 503, inspect backend logs for tenant readiness details (missing schema, migration mismatch, provisioning failed).
- If 503 is produced before the application, confirm `crm-backend` Service `targetPort` is `8000`, the container listens on `8000`, and readiness/liveness probes report ready endpoints.
- Confirm frontend base URL routes `/api` to the backend. For browser traffic behind ingress, avoid `localhost`/`127.0.0.1` in `VITE_API_BASE_URL`.
- If `/api/v1/platform/tenants` returns 401, ensure the platform UI is authenticated via `/api/v1/platform/auth/login` and sends the platform bearer token on all `/api/v1/platform/*` calls; redirect users to `/platform/login` on 401.

## Operational notes
- Roles: owner manages users and cash registers; admin handles catalog, stock, purchasing; cashier handles sales.
- Stock moves are append-only; never delete historical records.
- Cash register provider defaults to `mock`; configure a different provider via env or database row without changing business logic.
- Tenancy: API dependencies resolve the tenant from the request host subdomain after excluding `PLATFORM_HOSTS` and `RESERVED_SUBDOMAINS`. The selected tenant id is placed on `request.state.tenant_id`. JWTs must include a tenant claim that matches the resolved tenant. Requests for inactive tenants return 403; missing or unknown tenants fail fast before handler logic runs.
