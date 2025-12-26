# Engineering rules (must follow)

## 0. Golden rules
- No "creative" features beyond docs/*. Only implement what is specified.
- Keep code simple, explicit, and testable.
- No comments inside code. Documentation lives in docs/.
- Single source of truth for configs: .env + docs.

## 1. Tech stack (fixed)
### Backend
- Python 3.12
- FastAPI
- SQLAlchemy 2.x (async)
- Alembic for migrations
- Pydantic v2
- PostgreSQL 15+
- HTTP client: httpx
- Auth: JWT (access token) + refresh token (optional in MVP) OR session-based. Must be documented.

### Frontend (Web)
- TypeScript
- React + Vite OR Next.js (choose ONE, do not mix)
- UI: simple component library or minimal custom (choose ONE, do not mix)
- HTTP: fetch or axios (choose ONE, do not mix)
- State: React Query (recommended) or minimal state (choose ONE)

### Dev/Quality
- Formatting:
  - Backend: ruff + black
  - Frontend: eslint + prettier
- Tests:
  - Backend: pytest
  - Frontend: optional for MVP, but at least build/typecheck must pass
- DB migrations required for every schema change.

## 2. Repo structure (fixed)
/backend
/app
/api # routers
/core # settings, auth, deps
/db # session, base, migrations hooks
/models # SQLAlchemy models
/schemas # Pydantic schemas
/services # business logic
/repos # DB access layer / queries
main.py
/alembic
alembic.ini
pyproject.toml
README.md

/frontend
/src
/api # typed API clients
/pages # routes/pages
/components
/features # domain features (catalog, pos, reports)
/styles
package.json
vite.config.ts or next.config.js
README.md

/docs
... specs ...
10_engineering_rules.md
11_api_routes.md
12_db_schema.md
13_env_vars.md
14_runbook.md
15_decisions.md

## 3. Coding rules
### Backend
- Routers only handle HTTP concerns. Business logic in services/.
- DB access and queries in repos/. No raw SQL inside routers.
- All endpoints must be declared in docs/11_api_routes.md.
- Every DB table/column documented in docs/12_db_schema.md.
- Migrations:
  - never drop data by default
  - destructive operations must be explicit and documented

### Frontend
- Two UIs in one app:
  - Admin area
  - POS area (fast tile grid + cart)
- No duplicated business logic. Use shared api client and shared types.

## 4. Documentation rules (mandatory)
- docs/11_api_routes.md: full list of routes, payloads, responses, auth/roles.
- docs/12_db_schema.md: all tables, columns, indexes, constraints, relations.
- docs/13_env_vars.md: every env var with default and meaning.
- docs/14_runbook.md: how to run, migrate, seed data, troubleshoot.
- docs/15_decisions.md: all important tech decisions and why.

## 5. Definition of Done (DoD)
A feature is done only if:
- implemented
- covered by docs updates
- works end-to-end (frontend + backend + DB)
- passes format/lint/typecheck
- migrations included where needed
- no TODO placeholders left
