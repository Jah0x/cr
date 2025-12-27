import uuid
from datetime import datetime, timezone

from app.services.cash_register.base import CashRegister
from app.repos.cash_repo import CashReceiptRepo


class MockCashRegister(CashRegister):
    def __init__(self, receipt_repo: CashReceiptRepo):
        self.receipt_repo = receipt_repo

    async def open_shift(self):
        return {"status": "opened"}

    async def close_shift(self):
        return {"status": "closed"}

    async def sell(self, sale_id: str):
        receipt_id = f"mock-{uuid.uuid4()}"
        payload = {"sale_id": str(sale_id), "timestamp": datetime.now(timezone.utc).isoformat()}
        receipt = await self.receipt_repo.create(
            {"sale_id": sale_id, "receipt_id": receipt_id, "provider": "mock", "payload_json": payload}
        )
        return receipt

    async def refund(self, sale_id: str):
        receipt_id = f"mock-refund-{uuid.uuid4()}"
        payload = {"sale_id": str(sale_id), "timestamp": datetime.now(timezone.utc).isoformat(), "type": "refund"}
        receipt = await self.receipt_repo.create(
            {"sale_id": sale_id, "receipt_id": receipt_id, "provider": "mock", "payload_json": payload}
        )
        return receipt
