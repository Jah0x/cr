# Smoke check: tenant migrations + invites

## Database checks (psql)

Replace `<tenant_schema>` with the tenant schema name and run:

```sql
\dt public.*
\dt "<tenant_schema>".*
select * from "<tenant_schema>".alembic_version;
```

## Minimal flow

1. Create a tenant.
2. Run tenant migration (`POST /api/v1/platform/tenants/{id}/migrate`).
3. Create an invite (`POST /api/v1/platform/tenants/{id}/invite`) and capture the `invite_url`.
4. Open `/register?token=...` using the invite token and confirm:
   - `GET /api/v1/auth/invite-info?token=...` returns 200 with email/tenant/role.
   - `POST /api/v1/auth/register-invite` accepts the token and sets a password.
