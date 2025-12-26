# Roles & permissions

## Roles
### Owner
- Full access to everything
- Can change costing method, financial settings, users/roles, delete/close periods

### Manager
- Catalog management (categories, products, images, prices)
- Purchases & stock adjustments
- Reports & analytics
- Can NOT manage users/roles, and can NOT change system financial settings (costing method, close periods)

### Cashier
- POS only:
  - create sales
  - apply discounts (% or amount), within configured limits
  - mark payments (cash/card)
  - view product stock (optional: view only, no stock edits)
- No access to purchases, catalog editing, system settings

## Discount control
- System settings:
  - max discount percent per line and per receipt
  - max discount amount per line and per receipt
  - allow/deny manual price override
- Cashier: limited by those settings
- Manager/Owner: can override limits (configurable)
