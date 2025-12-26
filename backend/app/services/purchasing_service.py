from fastapi import HTTPException, status

from app.models.purchasing import PurchaseStatus
from app.repos.purchasing_repo import SupplierRepo, PurchaseInvoiceRepo, PurchaseItemRepo
from app.repos.stock_repo import StockRepo, StockBatchRepo


class PurchasingService:
    def __init__(self, supplier_repo: SupplierRepo, invoice_repo: PurchaseInvoiceRepo, item_repo: PurchaseItemRepo, stock_repo: StockRepo, batch_repo: StockBatchRepo):
        self.supplier_repo = supplier_repo
        self.invoice_repo = invoice_repo
        self.item_repo = item_repo
        self.stock_repo = stock_repo
        self.batch_repo = batch_repo

    async def list_suppliers(self):
        return await self.supplier_repo.list()

    async def create_supplier(self, data):
        return await self.supplier_repo.create(data)

    async def update_supplier(self, supplier_id, data):
        supplier = await self.supplier_repo.get(supplier_id)
        if not supplier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
        for key, value in data.items():
            if value is not None:
                setattr(supplier, key, value)
        return supplier

    async def delete_supplier(self, supplier_id):
        supplier = await self.supplier_repo.get(supplier_id)
        if not supplier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
        await self.supplier_repo.delete(supplier)

    async def create_invoice(self, data):
        return await self.invoice_repo.create(data)

    async def list_invoices(self, status_filter=None):
        return await self.invoice_repo.list(status_filter)

    async def get_invoice(self, invoice_id):
        invoice = await self.invoice_repo.get(invoice_id)
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        return invoice

    async def add_item(self, invoice_id, data):
        invoice = await self.get_invoice(invoice_id)
        if invoice.status != PurchaseStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit invoice")
        return await self.invoice_repo.add_item(invoice, data)

    async def post_invoice(self, invoice_id):
        invoice = await self.get_invoice(invoice_id)
        if invoice.status != PurchaseStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot post invoice")
        items = await self.item_repo.list_by_invoice(invoice.id)
        for item in items:
            await self.stock_repo.record_move(
                {"product_id": item.product_id, "quantity": item.quantity, "reason": "purchase", "reference": str(invoice.id)}
            )
            await self.batch_repo.create(
                {"product_id": item.product_id, "quantity": item.quantity, "unit_cost": item.unit_cost, "purchase_item_id": item.id}
            )
        invoice.status = PurchaseStatus.posted
        return invoice

    async def void_invoice(self, invoice_id):
        invoice = await self.get_invoice(invoice_id)
        invoice.status = PurchaseStatus.void
        return invoice
