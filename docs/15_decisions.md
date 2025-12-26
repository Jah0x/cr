# Decisions

- FastAPI is mounted under `/api/v1` with a dedicated health check for service monitoring.
- SQLAlchemy is configured in async mode with `asyncpg` to align with FastAPI's async request handling.
- Authentication uses stateless JWTs (HS256) carrying the user id in `sub`; access tokens expire based on `JWT_ACCESS_TTL_SECONDS`.
- There is no public registration; administrators create accounts via migrations or the owner bootstrap CLI.
- The bootstrap CLI seeds an `owner` role and ensures the configured owner account exists and remains active.
- The initial Alembic migration includes only the authentication tables to keep the first deployment minimal.
