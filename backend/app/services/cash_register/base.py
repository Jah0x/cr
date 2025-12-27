from abc import ABC, abstractmethod


class CashRegister(ABC):
    @abstractmethod
    async def open_shift(self):
        raise NotImplementedError

    @abstractmethod
    async def close_shift(self):
        raise NotImplementedError

    @abstractmethod
    async def sell(self, sale_id: str):
        raise NotImplementedError

    @abstractmethod
    async def refund(self, sale_id: str):
        raise NotImplementedError
