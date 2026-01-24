# Frontend

Install dependencies with `npm install` then run `npm run dev`.

Environment variables:
- `VITE_API_BASE_URL` to override the API base (default `/api/v1`).
- `VITE_PLATFORM_HOSTS` with comma-separated hostnames that should render the platform console.

Dev defaults:
- `frontend/.env.development` sets `VITE_API_BASE_URL=http://localhost:8000/api/v1` so the Vite dev server talks to the local backend.
