from fastapi import HTTPException, status
from sqlalchemy import select

from app.models.purchasing import PurchaseStatus
from app.models.stock import StockBatch
from app.repos.catalog_repo import ProductRepo
from app.repos.purchasing_repo import SupplierRepo, PurchaseInvoiceRepo, PurchaseItemRepo
from app.repos.stock_repo import StockRepo, StockBatchRepo


class PurchasingService:
    def __init__(
        self,
        supplier_repo: SupplierRepo,
        invoice_repo: PurchaseInvoiceRepo,
        item_repo: PurchaseItemRepo,
        stock_repo: StockRepo,
        batch_repo: StockBatchRepo,
        product_repo: ProductRepo,
    ):
        self.supplier_repo = supplier_repo
        self.invoice_repo = invoice_repo
        self.item_repo = item_repo
        self.stock_repo = stock_repo
        self.batch_repo = batch_repo
        self.product_repo = product_repo
        self.session = invoice_repo.session

    async def list_suppliers(self):
        return await self.supplier_repo.list()

    async def create_supplier(self, data):
        supplier = await self.supplier_repo.create(data)
        await self.session.refresh(supplier)
        return supplier

    async def update_supplier(self, supplier_id, data):
        supplier = await self.supplier_repo.get(supplier_id)
        if not supplier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
        for key, value in data.items():
            if value is not None:
                setattr(supplier, key, value)
        await self.session.flush()
        await self.session.refresh(supplier)
        return supplier

    async def delete_supplier(self, supplier_id):
        supplier = await self.supplier_repo.get(supplier_id)
        if not supplier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
        await self.supplier_repo.delete(supplier)

    async def create_invoice(self, data):
        invoice = await self.invoice_repo.create(data)
        await self.session.refresh(invoice)
        return invoice

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
        item = await self.invoice_repo.add_item(invoice, data)
        await self.session.refresh(invoice)
        return item

    async def post_invoice(self, invoice_id):
        invoice = await self.get_invoice(invoice_id)
        if invoice.status != PurchaseStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot post invoice")
        items = await self.item_repo.list_by_invoice(invoice.id)
        if not items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot post empty invoice")
        for item in items:
            await self.stock_repo.record_move(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "reason": "PURCHASE_IN",
                    "reference": str(invoice.id),
                }
            )
            await self.batch_repo.create(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_cost": item.unit_cost,
                    "purchase_item_id": item.id,
                }
            )
            product = await self.product_repo.get(item.product_id)
            if product:
                product.purchase_price = item.unit_cost
                if not product.cost_price or product.cost_price == 0:
                    product.cost_price = item.unit_cost
        invoice.status = PurchaseStatus.posted
        await self.session.flush()
        await self.session.refresh(invoice)
        return invoice

    async def void_invoice(self, invoice_id):
        invoice = await self.get_invoice(invoice_id)
        if invoice.status == PurchaseStatus.void:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invoice already void")
        if invoice.status == PurchaseStatus.posted:
            items = await self.item_repo.list_by_invoice(invoice.id)
            for item in items:
                await self.stock_repo.record_move(
                    {
                        "product_id": item.product_id,
                        "quantity": -item.quantity,
                        "reason": "PURCHASE_VOID",
                        "reference": str(invoice.id),
                    }
                )
                batches = await self.session.execute(
                    select(StockBatch).where(StockBatch.purchase_item_id == item.id)
                )
                for batch in batches.scalars():
                    if float(batch.quantity) < float(item.quantity):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot void purchase with consumed batches",
                        )
                    await self.session.delete(batch)
        invoice.status = PurchaseStatus.void
        await self.session.flush()
        await self.session.refresh(invoice)
        return invoice
