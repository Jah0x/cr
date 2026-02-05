from app.repos.stock_repo import StockRepo
from app.repos.store_repo import StoreRepo


class StockService:
    def __init__(self, stock_repo: StockRepo, store_repo: StoreRepo):
        self.stock_repo = stock_repo
        self.session = stock_repo.session
        self.store_repo = store_repo

    async def list_stock(self, product_id=None):
        levels = await self.stock_repo.list_on_hand(product_id)
        return [{"product_id": row.product_id, "on_hand": row.on_hand} for row in levels]

    async def list_moves(self, product_id=None):
        return await self.stock_repo.list_moves(product_id)

    async def adjust(self, data):
        payload = data.copy()
        if not payload.get("store_id"):
            payload["store_id"] = (await self.store_repo.get_default()).id
        move = await self.stock_repo.record_move(payload)
        await self.session.refresh(move)
        return move
