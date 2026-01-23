from app.core.config import get_settings
from app.services.cash_register.mock import MockCashRegister


def get_cash_register(receipt_repo, cash_register=None):
    settings = get_settings()
    provider = settings.cash_register_provider.lower()
    if cash_register:
        provider = cash_register.type.lower()
    if provider == "mock":
        return MockCashRegister(receipt_repo)
    raise ValueError("Unsupported cash register provider")
