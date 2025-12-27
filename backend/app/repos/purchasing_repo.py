from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.purchasing import Supplier, PurchaseInvoice, PurchaseItem, PurchaseStatus


class SupplierRepo:
    def __init__(self, session: AsyncSession, tenant_id):
        self.session = session
        self.tenant_id = tenant_id

    async def list(self) -> List[Supplier]:
        result = await self.session.execute(select(Supplier).where(Supplier.tenant_id == self.tenant_id))
        return result.scalars().all()

    async def create(self, data: dict) -> Supplier:
        payload = {**data, "tenant_id": self.tenant_id}
        supplier = Supplier(**payload)
        self.session.add(supplier)
        await self.session.flush()
        return supplier

    async def get(self, supplier_id) -> Optional[Supplier]:
        result = await self.session.execute(
            select(Supplier).where(Supplier.id == supplier_id, Supplier.tenant_id == self.tenant_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, supplier: Supplier) -> None:
        await self.session.delete(supplier)


class PurchaseInvoiceRepo:
    def __init__(self, session: AsyncSession, tenant_id):
        self.session = session
        self.tenant_id = tenant_id

    async def list(self, status: Optional[PurchaseStatus] = None) -> List[PurchaseInvoice]:
        stmt = select(PurchaseInvoice).where(PurchaseInvoice.tenant_id == self.tenant_id)
        if status:
            stmt = stmt.where(PurchaseInvoice.status == status)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: dict) -> PurchaseInvoice:
        payload = {**data, "tenant_id": self.tenant_id}
        invoice = PurchaseInvoice(**payload)
        self.session.add(invoice)
        await self.session.flush()
        return invoice

    async def get(self, invoice_id) -> Optional[PurchaseInvoice]:
        result = await self.session.execute(
            select(PurchaseInvoice).where(PurchaseInvoice.id == invoice_id, PurchaseInvoice.tenant_id == self.tenant_id)
        )
        return result.scalar_one_or_none()

    async def add_item(self, invoice: PurchaseInvoice, data: dict) -> PurchaseItem:
        payload = {**data, "invoice_id": invoice.id, "tenant_id": self.tenant_id}
        item = PurchaseItem(**payload)
        self.session.add(item)
        await self.session.flush()
        return item


class PurchaseItemRepo:
    def __init__(self, session: AsyncSession, tenant_id):
        self.session = session
        self.tenant_id = tenant_id

    async def list_by_invoice(self, invoice_id) -> List[PurchaseItem]:
        result = await self.session.execute(
            select(PurchaseItem).where(
                PurchaseItem.invoice_id == invoice_id, PurchaseItem.tenant_id == self.tenant_id
            )
        )
        return result.scalars().all()
