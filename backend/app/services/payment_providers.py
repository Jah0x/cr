from decimal import Decimal
from app.models.sales import PaymentProvider


class PaymentGateway:
    async def charge(self, provider: PaymentProvider, amount: Decimal, reference: str) -> str:
        return f"{provider.value}:{reference}:{amount}"
