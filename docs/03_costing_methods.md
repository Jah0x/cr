# Costing methods (COGS calculation)

We support 3 methods, selectable in system settings:
- LAST_PURCHASE (last known unit cost)
- WEIGHTED_AVERAGE (moving average per product)
- FIFO (consume oldest batches first)

## When COGS is computed
- At sale finalization (when payment is confirmed or sale is marked PAID).
- COGS is stored per SaleItem (cogs_total) to keep historical integrity even if future costs change.

## LAST_PURCHASE
- For each product keep last_purchase_unit_cost (updated on posted purchase).
- On sale finalize: cogs_total = abs(qty) * last_purchase_unit_cost.

## WEIGHTED_AVERAGE (moving average)
- Maintain per product:
  - avg_unit_cost
  - total_qty_on_hand
- On purchase posting:
  new_avg = (old_avg*old_qty + purchase_cost*purchase_qty) / (old_qty + purchase_qty)
- On sale finalize:
  cogs_total = abs(qty) * avg_unit_cost
  then reduce total_qty_on_hand

## FIFO
- On purchase posting create StockBatch with qty_remaining.
- On sale finalize consume batches in oldest-first order:
  - allocate quantities across batches
  - cogs_total = sum(consumed_qty * batch.unit_cost)
- Store allocations:
  - SaleItemCostAllocation: sale_item_id, batch_id, qty, unit_cost

## Negative stock rule
- By default, system forbids finalizing sale if it would drive stock below zero.
- Owner can enable "allow negative stock" (not recommended), but it must be explicit.
