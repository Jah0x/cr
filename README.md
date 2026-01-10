# Retail POS

Backend: FastAPI with PostgreSQL, SQLAlchemy, Alembic.
Frontend: React + Vite + React Query.

Use docker-compose to start PostgreSQL, backend, and frontend.

## Docker compose (recommended)

```bash
docker compose up -d --build
```

### Check services

* Health: `http://localhost/api/v1/health`
* Login: open `http://localhost`, sign in, and confirm the UI shows the authenticated state or user data.

## Backend sanity checks (manual)

From the repo root:

```bash
docker-compose up -d db
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app
cd backend
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
