from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shifts import CashierShiftStatus
from app.repos.shifts_repo import CashierShiftRepo


class ShiftsService:
    def __init__(self, session: AsyncSession, shift_repo: CashierShiftRepo):
        self.session = session
        self.shift_repo = shift_repo

    async def open_shift(self, cashier_id, payload: dict):
        active = await self.shift_repo.get_active_for_cashier(cashier_id)
        if active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "Cashier already has active shift", "current_shift_id": str(active.id)},
            )
        shift = await self.shift_repo.create(
            {
                "store_id": payload["store_id"],
                "cashier_id": cashier_id,
                "opening_cash": payload.get("opening_cash") or 0,
                "note": payload.get("note"),
                "status": CashierShiftStatus.open,
            }
        )
        return shift

    async def close_shift(self, shift_id, payload: dict, current_user):
        shift = await self.shift_repo.get(shift_id)
        if not shift:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")
        role_names = {role.name.lower() for role in current_user.roles}
        if shift.cashier_id != current_user.id and "owner" not in role_names:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        if shift.status != CashierShiftStatus.open:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Shift already closed")
        shift.status = CashierShiftStatus.closed
        shift.closed_at = datetime.now(timezone.utc)
        if payload.get("closing_cash") is not None:
            shift.closing_cash = payload["closing_cash"]
        if payload.get("note") is not None:
            shift.note = payload["note"]
        await self.session.flush()
        return shift

    async def get_active(self, cashier_id):
        return await self.shift_repo.get_active_for_cashier(cashier_id)

    async def list_shifts(self, *, store_id=None, date_from=None, date_to=None, cashier_id=None, status=None):
        return await self.shift_repo.list(store_id, date_from, date_to, cashier_id, status)

    async def get_shift(self, shift_id):
        shift = await self.shift_repo.get(shift_id)
        if not shift:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")
        sales = await self.shift_repo.list_sales(shift_id)
        aggregates = await self.shift_repo.get_aggregates(shift_id)
        return {"shift": shift, "sales": sales, "aggregates": aggregates}
