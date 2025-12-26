from fastapi import HTTPException, status

from app.core.config import settings
from app.models.sales import SaleStatus
from app.repos.sales_repo import SaleRepo, SaleItemRepo, PaymentRepo
from app.repos.stock_repo import StockRepo, StockBatchRepo
from app.services.payment_providers import PaymentGateway


class SalesService:
    def __init__(self, sale_repo: SaleRepo, item_repo: SaleItemRepo, payment_repo: PaymentRepo, stock_repo: StockRepo, batch_repo: StockBatchRepo, gateway: PaymentGateway):
        self.sale_repo = sale_repo
        self.item_repo = item_repo
        self.payment_repo = payment_repo
        self.stock_repo = stock_repo
        self.batch_repo = batch_repo
        self.gateway = gateway

    async def create_sale(self, data):
        return await self.sale_repo.create(data)

    async def get_sale(self, sale_id):
        sale = await self.sale_repo.get(sale_id)
        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")
        return sale

    async def add_item(self, sale_id, data):
        sale = await self.get_sale(sale_id)
        if sale.status != SaleStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit sale")
        return await self.item_repo.add(sale.id, data)

    async def update_item(self, item_id, data):
        item = await self.item_repo.get(item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        for key, value in data.items():
            if value is not None:
                setattr(item, key, value)
        return item

    async def add_payment(self, sale_id, data):
        sale = await self.get_sale(sale_id)
        if sale.status != SaleStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot pay finalized sale")
        reference = await self.gateway.charge(data["provider"], data["amount"], data.get("reference", ""))
        payload = data | {"reference": reference}
        return await self.payment_repo.add(sale.id, payload)

    async def finalize(self, sale_id):
        sale = await self.get_sale(sale_id)
        if sale.status != SaleStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already finalized")
        items = sale.items
        for item in items:
            try:
                consumed = await self.batch_repo.consume(item.product_id, float(item.quantity))
            except ValueError:
                if settings.allow_negative_stock:
                    consumed = []
                else:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")
            if not consumed and settings.allow_negative_stock:
                await self.stock_repo.record_move(
                    {"product_id": item.product_id, "quantity": -item.quantity, "reason": "sale", "reference": str(sale.id)}
                )
            for batch, qty in consumed:
                await self.stock_repo.record_move(
                    {"product_id": item.product_id, "quantity": -qty, "reason": "sale", "reference": str(sale.id)}
                )
                batch.quantity = batch.quantity
            sale.status = SaleStatus.finalized
        return sale

    async def void_sale(self, sale_id):
        sale = await self.get_sale(sale_id)
        sale.status = SaleStatus.void
        return sale
