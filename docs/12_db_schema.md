# Database schema (PostgreSQL)

## Conventions
- Primary keys: UUID
- created_at / updated_at: timestamptz
- Monetary: numeric(12,2)
- Quantity: numeric(12,3)

## Tables
(Each table must list:)
- columns (name, type, nullable, default)
- indexes
- constraints
- relations

### users
### roles
### user_roles

### categories
### brands
### product_lines
### products

### suppliers
### purchase_invoices
### purchase_items

### stock_moves
### stock_batches
### sale_item_cost_allocations (for FIFO)

### sales
### sale_items
### payments

## Views (optional)
- v_stock_on_hand
- v_sales_summary
