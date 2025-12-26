from fastapi import HTTPException, status

from app.repos.stock_repo import StockRepo


class StockService:
    def __init__(self, stock_repo: StockRepo):
        self.stock_repo = stock_repo

    async def list_stock(self, product_id=None):
        moves = await self.stock_repo.list_moves(product_id)
        on_hand = {}
        for move in moves:
            on_hand[move.product_id] = on_hand.get(move.product_id, 0) + float(move.quantity)
        return [{"product_id": pid, "on_hand": qty} for pid, qty in on_hand.items()]

    async def list_moves(self, product_id=None):
        return await self.stock_repo.list_moves(product_id)

    async def adjust(self, data):
        move = await self.stock_repo.record_move(data)
        return move
