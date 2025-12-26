# Runbook

## Setup
1. Start PostgreSQL locally or with Docker: `docker compose up -d db` from the repo root.
2. Set environment variables from `docs/13_env_vars.md`, including `DATABASE_URL` with the `postgresql+asyncpg://` driver and a `JWT_SECRET` value.
3. Install backend dependencies: `cd backend && poetry install`.
4. Apply migrations to a fresh database: `cd backend && poetry run alembic upgrade head`.
5. Create the bootstrap owner after migrations: `cd backend && poetry run python -m app.cli create-owner`.

## Database operations
- Generate a migration after model changes: `cd backend && poetry run alembic revision --autogenerate -m "<message>"`.
- Apply migrations in any environment: `cd backend && poetry run alembic upgrade head`.
- Check the current revision: `cd backend && poetry run alembic current`.

## Running the API
- Start the app: `cd backend && poetry run uvicorn app.main:app --host $APP_HOST --port $APP_PORT`.
- Health check: `GET /api/v1/health`.
- Login: `POST /api/v1/auth/login` with JSON `{ "email": FIRST_OWNER_EMAIL, "password": FIRST_OWNER_PASSWORD }`.
- Use the returned bearer token for `GET /api/v1/auth/me`.

## Operational notes
- The owner seeding task is idempotent; rerun it safely after resetting credentials or databases.
- Tokens are stateless; rotate `JWT_SECRET` to invalidate existing sessions.
