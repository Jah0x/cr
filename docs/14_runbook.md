# Runbook

## Dev prerequisites
- Python 3.12
- Node 20+
- PostgreSQL 15+
- Docker + docker compose (for local dependencies)

## Bring up dependencies
- Start Postgres (and optional app containers) with docker compose:
  - `docker compose up -d db`
  - `docker compose up -d` (to run db + backend + frontend together)
- Inspect container status: `docker compose ps`
- Tail container logs when debugging: `docker compose logs -f db`

## Backend dev
- Create and activate the virtualenv (from `backend`):
  - `cd backend`
  - `poetry install`
- Copy or set `.env` values as listed in `docs/13_env_vars.md`. Minimum for local dev:
  - `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app`
  - `JWT_SECRET=changeme`
- Apply migrations (after DB is up): `poetry run alembic upgrade head`
- Start the API server: `poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

## Frontend dev
- Install dependencies (from `frontend`):
  - `cd frontend`
  - `npm install`
- Ensure API base URL is set (e.g., `.env.local`):
  - `VITE_API_BASE_URL=http://localhost:8000/api/v1`
- Start dev server: `npm run dev -- --host --port 4173`

## DB migrations
- Create a new migration (after model changes): `poetry run alembic revision --autogenerate -m "short message"`
- Apply latest migration: `poetry run alembic upgrade head`
- Roll back one step: `poetry run alembic downgrade -1`

## Seed data
- Create owner user via CLI (requires DB + migrations):
  - `cd backend`
  - `poetry run python - <<'PY'
import asyncio
from sqlalchemy import select
from app.core.db import async_session
from app.core.security import hash_password
from app.models.user import Role, User, UserRole

async def main():
    async with async_session() as session:
        owner_role = await session.scalar(select(Role).where(Role.name == "owner"))
        if not owner_role:
            owner_role = Role(name="owner")
            session.add(owner_role)
            await session.flush()
        email = "owner@example.com"
        password = "admin123"
        user = await session.scalar(select(User).where(User.email == email))
        if not user:
            user = User(email=email, password_hash=hash_password(password))
            session.add(user)
            await session.flush()
            session.add(UserRole(user_id=user.id, role_id=owner_role.id))
        await session.commit()
        print(f"Owner user ready: {email}")

asyncio.run(main())
PY`
- Seed starter catalog data (optional):
  - `poetry run python - <<'PY'
import asyncio
from sqlalchemy import select
from app.core.db import async_session
from app.models.catalog import Brand, Category, Product, ProductLine

async def main():
    async with async_session() as session:
        electronics = await session.scalar(select(Category).where(Category.name == "Electronics"))
        if not electronics:
            electronics = Category(name="Electronics")
            session.add(electronics)
        acme = await session.scalar(select(Brand).where(Brand.name == "ACME"))
        if not acme:
            acme = Brand(name="ACME")
            session.add(acme)
            await session.flush()
        gadgets = await session.scalar(select(ProductLine).where(ProductLine.name == "Gadgets"))
        if not gadgets:
            gadgets = ProductLine(name="Gadgets", brand_id=acme.id)
            session.add(gadgets)
            await session.flush()
        demo = await session.scalar(select(Product).where(Product.sku == "SKU-001"))
        if not demo:
            demo = Product(sku="SKU-001", name="Demo Widget", category_id=electronics.id, brand_id=acme.id, line_id=gadgets.id, price=199.99)
            session.add(demo)
        await session.commit()
        print("Seed data applied")

asyncio.run(main())
PY`

## Troubleshooting
- DB connection refused: ensure `docker compose up -d db` is running and `DATABASE_URL` host matches (`localhost` outside docker, `db` inside compose).
- Alembic cannot import settings: confirm `.env` exists in `backend/` and variables match `docs/13_env_vars.md`.
- Migration locked or failed: run `docker compose restart db`, then re-run `poetry run alembic upgrade head`.
- Backend port busy: stop other services on `8000` or change `APP_PORT`/`uvicorn --port` and update `VITE_API_BASE_URL`.
- Frontend cannot reach API: verify CORS origins include your frontend host and confirm API URL in `.env.local`.
