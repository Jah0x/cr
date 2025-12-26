# API routes (v1)

Base path: `/api/v1`

## Health
- **GET /health** — public liveness probe. Response: `{ "status": "ok" }`.

## Auth
- **POST /auth/login** — anonymous. Payload: `{ "email": string, "password": string }`. Response: `{ "access_token": string, "token_type": "bearer" }`.
- **GET /auth/me** — requires `Authorization: Bearer <access_token>`. Response: `{ "id": uuid, "email": string }`.

Notes:
- There is no public registration endpoint. Accounts are provisioned through migrations or CLI tasks.
