# Implementation phases

Phase 1: DB + Auth + Roles
- schema + migrations
- users/roles + permissions middleware

Phase 2: Catalog
- categories/brands/lines/products
- product images as URL/path

Phase 3: Purchasing + Stock base
- suppliers + purchase invoices
- posting creates stock batches and stock moves

Phase 4: POS sales
- OPEN sale, items, discounts, finalize
- stock validation, movements
- payments, PAID state

Phase 5: Costing methods
- LAST_PURCHASE first
- WEIGHTED_AVERAGE next
- FIFO with batch allocations

Phase 6: Reports
- summary + slices + top products + stock alerts

Phase 7: Terminal integration (optional)
- define provider adapter once provider is known
