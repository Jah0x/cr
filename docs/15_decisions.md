# Decisions

- API served under `/api/v1` with standalone `/healthz` and `/readyz` for probes; readiness hits the DB.
- Async SQLAlchemy with asyncpg remains the persistence layer to keep parity with FastAPI async handlers.
- Auth uses stateless HS256 JWT containing `sub` and `roles`; expiry driven by `JWT_EXPIRES`.
- No public signup. Owners manage all user provisioning via the `/users` endpoints; bootstrap seeds the first owner only when the database is empty.
- Roles are explicit (`owner`, `admin`, `cashier`) and enforced at router level: owner manages users and cash registers; admin covers catalog/stock/purchasing; cashier handles sales.
- Cash registers are modular: business logic consumes an abstract interface; a mock provider is default and registers are stored in `cash_registers` to allow future pluggable providers without altering services.
- Sales are transactional: item creation, stock deductions, payments, and receipt registration happen in a single DB transaction; refunds/voids always append stock history and receipts.
