# AGENTS.md

## Purpose
This repository is a Vite + React + TypeScript retail/POS app with Prisma and SQLite. Use this file as the working contract for Codex. Keep changes small, verifiable, and consistent with the existing architecture.

## What matters most
- Preserve working retail flows before optimizing UX.
- Inventory quantities are integers only. Never introduce fractional stock.
- Prefer backward-compatible changes when touching stock, sales, purchasing, or product data.
- When a task affects database shape, update schema, migrations, server logic, client types, mock client, and tests together.
- Do not ship UI-only changes that fake business logic for stock, catalog, or purchasing.

## Current project map
- `package.json` — Vite app, TypeScript, Prisma, ESLint.
- `prisma/schema.prisma` — source of truth for data models.
- `api.ts` — main server-side business logic used by the app.
- `src/shared/lib/apiClient.ts` — mock/local API client used by current frontend flows; keep it in sync with changed DTOs during frontend work.
- `src/shared/lib/formatters.ts` — centralized formatting helpers.
- `src/entities/product/model/types.ts` — frontend product types.
- `src/entities/product/ui/*` — product presentation components.
- `src/features/product-crud/*` — add/edit/restock product flows.
- `src/pages/products/index.tsx` — admin product page.

## Domain rules
- Product catalog must support a base product with variants/flavors.
- Variant is the stock-bearing unit unless a task explicitly keeps legacy behavior during migration.
- Public catalog may aggregate by base product, but stock accounting must stay correct at variant level.
- Stock movement must be auditable. Never mutate stock silently without creating or preserving an audit trail.
- Money formatting can be localized, but quantity formatting must stay integer and human-readable.

## Required engineering behavior
- Read the relevant files before editing.
- Trace the end-to-end path before changing behavior:
  - schema/data model
  - server logic
  - client DTO/types
  - UI state/forms
  - tests/manual verification
- If a task is large, write a short execution plan in `docs/exec-plans/<slug>.md` and keep this file short.
- If instructions conflict, prefer user request, then safety/data integrity, then local code style.

## Database changes
- Use Prisma migrations; do not hand-edit production data without a script.
- For any inventory migration, provide:
  - dry-run mode
  - apply mode
  - clear logging
  - rollback/backout notes
- Never delete old inventory/audit data unless the task explicitly requires archival/removal.
- For risky data changes, keep temporary compatibility fields until the app is fully migrated.

## API and server rules
- Keep `api.ts` behavior explicit and boring.
- Validate inputs at boundaries.
- Reject invalid stock quantities, especially fractional values.
- Prefer transactional writes for product+variant creation, stock adjustments, and purchasing flows.
- Do not introduce hidden magic defaults that make inventory ambiguous.

## Frontend rules
- Reuse existing shared UI primitives first.
- Keep forms understandable for non-technical retail staff.
- Default to fewer clicks and clearer labels over visual cleverness.
- When adding a new DTO shape, update:
  - `src/entities/product/model/types.ts`
  - `src/shared/lib/apiClient.ts`
  - relevant feature hooks/components
- Keep empty/loading/error states obvious.
- Avoid displaying `1.000`, `8.000`, etc. Quantities should render as `1`, `8`, `15`.

## Catalog and inventory UX rules
- Base product groups flavors/variants.
- Variant picker must be explicit anywhere stock is reserved, purchased, sold, or adjusted.
- Purchasing UI should support batch entry of several variants of the same base product in one flow.
- Public catalog should stay simple: user sees the product first, then available variants.
- Admin UI should favor inventory clarity over marketing presentation.

## Testing and verification
Before finishing any non-trivial task, run as many of these as apply:
- `npm run lint`
- `npm run build`
- `npx prisma generate`
- relevant migration command(s)
- targeted manual flow checks for product create/edit/restock/catalog/purchase

For inventory or schema tasks, also verify manually:
- product creation
- variant creation/editing
- stock increase/decrease
- stock history/audit trail
- catalog visibility
- no fractional quantity leaks into UI

## Change scope discipline
- Do not refactor unrelated modules in the same patch.
- Do not rename broad folders/files without strong reason.
- Do not switch state-management or API patterns unless the task explicitly asks for it.
- If a mock client is masking real backend issues, note it in the summary and keep both sides consistent.

## Output expectations
When you finish:
- summarize what changed
- list migrations/scripts added
- list commands run
- list tests/checks performed
- list unresolved risks or follow-ups

## PR hygiene
- Use descriptive commit messages.
- Keep diffs reviewable.
- Include a short operator-facing note when behavior changes in purchasing, stock, or catalog.
