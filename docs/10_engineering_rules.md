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
