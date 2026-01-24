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
2. Run tenant migration.
3. Create an invite.
4. Register using `/register?token=...`.
