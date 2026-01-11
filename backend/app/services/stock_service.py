from app.repos.stock_repo import StockRepo


class StockService:
    def __init__(self, stock_repo: StockRepo):
        self.stock_repo = stock_repo
        self.session = stock_repo.session

    async def list_stock(self, product_id=None):
        levels = await self.stock_repo.list_on_hand(product_id)
        return [{"product_id": row.product_id, "on_hand": row.on_hand} for row in levels]

    async def list_moves(self, product_id=None):
        return await self.stock_repo.list_moves(product_id)

    async def adjust(self, data):
        move = await self.stock_repo.record_move(data)
        await self.session.refresh(move)
        return move
