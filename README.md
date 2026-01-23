# Retail POS

Backend: FastAPI with PostgreSQL, SQLAlchemy, Alembic.
Frontend: React + Vite + React Query.

## Kubernetes run (conceptual)

1. Build and publish the backend/frontend container images.
2. Provision PostgreSQL (managed service or StatefulSet) and expose it to the backend.
3. Create Kubernetes Deployments for backend and frontend, plus Services and an Ingress (or Gateway) for routing.
4. Configure the backend with the required environment variables (see below).
5. Run database migrations as a one-off Job or `kubectl exec` using:
   `python -m app.cli migrate-all` (full backend) or `python -m app.migrator.main` (public-only migrator).
6. Roll out the backend and frontend Deployments.

### Required environment variables

* `DATABASE_URL`
* `JWT_SECRET`
* `ROOT_DOMAIN` (e.g. `securesoft.dev`)
* `PLATFORM_HOSTS` (e.g. `crm.securesoft.dev`)
* `RESERVED_SUBDOMAINS` (e.g. `crm,platform,www,api`)
* `DEFAULT_TENANT_SLUG`
* `FIRST_OWNER_EMAIL`
* `FIRST_OWNER_PASSWORD`
* `BOOTSTRAP_TOKEN` (optional fallback for platform auth)

### Migrator environment variables

* `DATABASE_URL`

### Migrator command

`python -m app.migrator.main`

### Public migrations behavior

* Public migrations are applied via `alembic upgrade head` (no branch labels).
* Alembic branches are not used for public migrations; `versions/public` is treated as the public migration source.

### Kubernetes Job (migrations)

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: crm-migrator
  namespace: crm
spec:
  backoffLimit: 0
  ttlSecondsAfterFinished: 3600
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migrator
          image: ghcr.io/your-org/crm-migrator:latest
          imagePullPolicy: Always
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: crm-database
                  key: DATABASE_URL
          command: ["python", "-m", "app.migrator.main"]
```

## Frontend API base URL

The frontend defaults to using `/api/v1` for API requests. You can override this at build time by setting `VITE_API_BASE_URL`.

```bash
VITE_API_BASE_URL=/api/v1
```

## Frontend runtime configuration

The frontend attempts to load `/config.json` at startup (no cache) for runtime overrides. This is useful for configuring platform/tenant hosts without rebuilding the image. Example:

```json
{
  "platformHosts": ["crm.securesoft.dev"],
  "rootDomain": "securesoft.dev",
  "apiBase": "/api/v1"
}
```

In Kubernetes, provide this file via a ConfigMap and mount it at `/usr/share/nginx/html/config.json` inside the frontend container.

You can also set `VITE_PLATFORM_HOSTS` at build time to the same host list (comma-separated). Platform UI is enabled only for hosts listed in `platformHosts`/`VITE_PLATFORM_HOSTS`.

## Platform/auth endpoints

* `POST /api/v1/platform/auth/login` — login with the configured platform owner email/password.
* `POST /api/v1/platform/tenants` — returns `tenant_url` and `invite_url` for first-user registration.
* `GET /api/v1/auth/invite-info` — validates invite token for tenant registration.
* `POST /api/v1/auth/register-invite` — completes tenant owner registration and returns a tenant JWT.

### Check services

* Health: `http://localhost/api/v1/health`
* Login: open `http://localhost`, sign in, and confirm the UI shows the authenticated state or user data.
