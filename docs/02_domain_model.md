# Domain model (core entities)

## Catalog
- Category (tree): id, name, parent_id
- Brand: id, name
- ProductLine: id, brand_id, name
- Product:
  - id, name
  - category_id
  - brand_id (optional)
  - line_id (optional)
  - image_url (optional)
  - is_active
  - sell_price_default (recommended)
  - sku/barcode (recommended)
  - created_at

## Purchasing (stock in)
- Supplier: id, name, contacts (optional)
- PurchaseInvoice:
  - id, supplier_id, doc_no, doc_date
  - status: DRAFT | POSTED | VOID
  - posted_at
  - comment
- PurchaseItem:
  - invoice_id, product_id
  - qty
  - unit_cost (purchase cost per unit)
  - optional: tax/fees fields (non-MVP by default)

Posting a PurchaseInvoice creates stock batches (for FIFO/AVG) and stock movements.

## Stock
We store both:
1) Stock movements ledger (auditable)
2) Costing layers/batches (for FIFO/AVG computation)

- StockMove:
  - id, product_id
  - type: PURCHASE_IN | SALE_OUT | ADJUST | WRITE_OFF | RETURN_IN
  - qty (signed convention allowed, but store normalized)
  - unit_cost_snapshot
  - unit_sell_snapshot
  - ref_type/ref_id (links to invoice/sale/adjustment)
  - created_at
  - comment

- StockBatch (cost layer):
  - id, product_id
  - source_type/source_id (PurchaseInvoice)
  - qty_in
  - qty_remaining
  - unit_cost
  - received_at

## Sales (POS)
- Sale:
  - id, created_at
  - status: OPEN | PAID | VOID
  - cashier_user_id
  - discount_total_amount (optional)
  - payment_status: UNPAID | PARTIAL | PAID
  - totals: subtotal, discount_total, total_due, total_paid
- SaleItem:
  - sale_id, product_id
  - qty
  - unit_price (sell price used)
  - discount_percent (optional)
  - discount_amount (optional)
  - line_subtotal, line_discount, line_total
  - cogs_total (computed at finalization)
- Payment:
  - id, sale_id
  - method: CASH | CARD | MIXED (optional)
  - amount
  - provider (optional)
  - external_ref (optional: terminal transaction id)
  - status: INITIATED | SUCCESS | FAILED (optional)
  - created_at

## Accounting results we track
- Turnover: sum of paid sales totals in period
- COGS: cost of goods sold, computed at sale finalization based on costing method
- Gross profit: turnover - COGS
- Margin: gross profit / turnover
