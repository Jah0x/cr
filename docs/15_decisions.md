# Decisions

- API served under `/api/v1` with standalone `/healthz` and `/readyz` for probes; readiness hits the DB.
- Async SQLAlchemy with asyncpg remains the persistence layer to keep parity with FastAPI async handlers.
- Auth uses stateless HS256 JWT containing `sub`, `roles`, and a required `tenant_id`; expiry driven by `JWT_EXPIRES` and tokens are rejected if the tenant claim is absent or mismatched with the active tenant.
- No public signup. Owners manage all user provisioning via the `/users` endpoints; bootstrap seeds the first owner only when the database is empty.
- Roles are explicit (`owner`, `admin`, `cashier`) and enforced at router level: owner manages users and cash registers; admin covers catalog/stock/purchasing; cashier handles sales.
- Cash registers are modular: business logic consumes an abstract interface; a mock provider is default and registers are stored in `cash_registers` to allow future pluggable providers without altering services.
- Sales are transactional: item creation, stock deductions, payments, and receipt registration happen in a single DB transaction; refunds/voids always append stock history and receipts.
- Tenant resolution is centralized in a FastAPI dependency that derives the tenant from the request host subdomain after excluding platform hosts and reserved subdomains; inactive tenants are rejected early and the resolved tenant id is stored on `request.state`.
- Platform-only provisioning uses platform-scoped JWTs (fallback: `BOOTSTRAP_TOKEN`) to gate admin routes for creating tenants and applying templates; modules, templates, and tenant-module/feature mappings live in the public schema.
- Host-based mode detection drives the UX: platform hosts render the platform console, tenant hosts render tenant routes, and backend module/feature toggles enforce visibility + access across UI and APIs.
