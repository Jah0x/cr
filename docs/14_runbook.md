# Runbook

## Setup
1. Install dependencies: `cd backend && poetry install`.
2. Configure environment variables from `docs/13_env_vars.md`. Use an async URL with `+asyncpg`.
3. Apply migrations: `cd backend && poetry run alembic upgrade head`.
4. Create the bootstrap owner: `cd backend && poetry run python -m app.cli create-owner`.

## Running the API
- Start the app: `cd backend && poetry run uvicorn app.main:app --host $APP_HOST --port $APP_PORT`.
- Health check: `GET /api/v1/health`.
- Login: `POST /api/v1/auth/login` with JSON `{ "email": FIRST_OWNER_EMAIL, "password": FIRST_OWNER_PASSWORD }`.
- Use the returned bearer token for `GET /api/v1/auth/me`.

## Operational notes
- The owner seeding task is idempotent; rerun it safely after resetting credentials or databases.
- Tokens are stateless; rotate `JWT_SECRET` to invalidate existing sessions.
