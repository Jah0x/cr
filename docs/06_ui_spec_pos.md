# Web POS UI (cashier)

## Layout
- Left: category tree (fast select)
- Optional second row: brand/line filters for certain categories
- Top: search bar
- Main: product tiles grid (square)
  - image, name, price, stock badge
- Right panel: current receipt/cart
  - items list
  - qty +/- controls
  - discount per line: % or amount
  - receipt discount: % or amount (if enabled)
  - totals: subtotal, discount, due

## Checkout flow
- Choose payment method: Cash / Card
- If Card:
  - either "initiate payment" (if provider supports)
  - or "mark as paid" with external_ref (manual)
- Finalize -> sale becomes PAID
