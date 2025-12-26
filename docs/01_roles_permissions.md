# Roles & permissions

## Roles

### Owner
- Full access to everything
- Can change costing method, financial settings, users/roles
- Can override discount limits and stock rules

### Manager
- Catalog management (categories, products, images, prices)
- Purchases & stock adjustments / write-offs
- Reports & analytics
- Can confirm TRANSFER payments
- Cannot manage users/roles
- Cannot change costing method (owner only)

### Cashier
- POS only:
  - create sales
  - apply discounts (% or amount) within configured limits
  - take payments (CASH/CARD), create TRANSFER as "pending"
  - view product stock (optional: view only, no stock edits)
- Cannot confirm TRANSFER by default
- No access to purchases, catalog editing, system settings

## Discount control
- System settings:
  - max discount percent per line and per receipt
  - max discount amount per line and per receipt
  - allow/deny manual price override
- Cashier: limited by those settings
- Manager/Owner: can override (configurable)

## Payments rules
- Payment methods: CASH, CARD, TRANSFER
- TRANSFER defaults to INITIATED and must be confirmed by Manager/Owner
- Sale can be finalized only when total_paid >= total_due and required confirmations are done

## Stock rule
- Default: forbid negative stock on sale finalization
- Owner can explicitly enable allow_negative_stock
