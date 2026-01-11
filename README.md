# Retail POS

Backend: FastAPI with PostgreSQL, SQLAlchemy, Alembic.
Frontend: React + Vite + React Query.

## Kubernetes run (conceptual)

1. Build and publish the backend/frontend container images.
2. Provision PostgreSQL (managed service or StatefulSet) and expose it to the backend.
3. Create Kubernetes Deployments for backend and frontend, plus Services and an Ingress (or Gateway) for routing.
4. Configure the backend with the required environment variables (see below).
5. Run database migrations as a one-off Job or `kubectl exec` using:
   `python -m app.cli migrate-all`.
6. Roll out the backend and frontend Deployments.

### Required environment variables

* `DATABASE_URL`
* `JWT_SECRET`
* `ROOT_DOMAIN`
* `PLATFORM_HOSTS`
* `RESERVED_SUBDOMAINS`
* `DEFAULT_TENANT_SLUG`
* `FIRST_OWNER_EMAIL`
* `FIRST_OWNER_PASSWORD`
* `BOOTSTRAP_TOKEN`

## Frontend API base URL

The frontend defaults to using `/api/v1` for API requests. You can override this at build time by setting `VITE_API_BASE_URL`.

```bash
VITE_API_BASE_URL=/api/v1
```

### Check services

* Health: `http://localhost/api/v1/health`
* Login: open `http://localhost`, sign in, and confirm the UI shows the authenticated state or user data.
