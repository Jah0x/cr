from abc import ABC, abstractmethod


class CashRegister(ABC):
    @abstractmethod
    async def open_shift(self):
        raise NotImplementedError

    @abstractmethod
    async def close_shift(self):
        raise NotImplementedError

    @abstractmethod
    async def register_sale(self, sale_id: str):
        raise NotImplementedError

    @abstractmethod
    async def refund_sale(self, sale_id: str):
        raise NotImplementedError
