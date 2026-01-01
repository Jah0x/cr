# Retail POS

Backend: FastAPI with PostgreSQL, SQLAlchemy, Alembic.
Frontend: React + Vite + React Query.

Use docker-compose to start PostgreSQL, backend, and frontend.

## Backend sanity checks (manual)

From the repo root:

```bash
docker-compose up -d db
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app
cd backend
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
