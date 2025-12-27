from app.core.config import settings
from app.services.cash_register.mock import MockCashRegister


def get_cash_register(receipt_repo):
    provider = settings.cash_register_provider.lower()
    if provider == "mock":
        return MockCashRegister(receipt_repo)
    raise ValueError("Unsupported cash register provider")
