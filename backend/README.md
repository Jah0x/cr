# Backend

Set `DATABASE_URL` with the `postgresql+asyncpg://` driver and `JWT_SECRET`, then install dependencies with `poetry install`.

Apply migrations with `poetry run alembic upgrade head`.

Run the API with `poetry run uvicorn app.main:app --reload`.
