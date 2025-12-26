# Database schema

Alembic revision `0001_initial` creates the authentication tables.

## users
- `id` — UUID primary key.
- `email` — unique email address.
- `password_hash` — bcrypt hash.
- `is_active` — boolean flag for login eligibility.

## roles
- `id` — UUID primary key.
- `name` — unique role name.

## user_roles
- `user_id` — references `users.id`, cascade delete.
- `role_id` — references `roles.id`, cascade delete.

All UUID defaults are generated in the application layer.
