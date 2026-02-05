from datetime import datetime
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_tenant, get_current_user, get_db_session, require_module, require_roles
from app.models.shifts import CashierShiftStatus
from app.repos.shifts_repo import CashierShiftRepo
from app.schemas.shifts import ShiftCloseIn, ShiftDetail, ShiftOpenIn, ShiftOut
from app.services.shifts_service import ShiftsService

router = APIRouter(
    prefix="/shifts",
    tags=["shifts"],
    dependencies=[
        Depends(require_roles({"owner", "cashier"})),
        Depends(get_current_tenant),
        Depends(require_module("sales")),
    ],
)


def get_service(session: AsyncSession):
    return ShiftsService(session, CashierShiftRepo(session))


@router.post("", response_model=ShiftOut)
async def open_shift(
    payload: ShiftOpenIn,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await get_service(session).open_shift(current_user.id, payload.model_dump())


@router.post("/{shift_id}/close", response_model=ShiftOut)
async def close_shift(
    shift_id: uuid.UUID,
    payload: ShiftCloseIn,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await get_service(session).close_shift(shift_id, payload.model_dump(), current_user)


@router.get("/active", response_model=ShiftOut | None)
async def get_active_shift(
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await get_service(session).get_active(current_user.id)


@router.get("", response_model=list[ShiftOut])
async def list_shifts(
    store_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    cashier_id: uuid.UUID | None = None,
    status: CashierShiftStatus | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    return await get_service(session).list_shifts(
        store_id=store_id,
        date_from=date_from,
        date_to=date_to,
        cashier_id=cashier_id,
        status=status,
    )


@router.get("/{shift_id}", response_model=ShiftDetail)
async def get_shift(
    shift_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
):
    data = await get_service(session).get_shift(shift_id)
    shift = data["shift"]
    return {
        "id": shift.id,
        "store_id": shift.store_id,
        "cashier_id": shift.cashier_id,
        "opened_at": shift.opened_at,
        "closed_at": shift.closed_at,
        "status": shift.status,
        "opening_cash": shift.opening_cash,
        "closing_cash": shift.closing_cash,
        "note": shift.note,
        "aggregates": data["aggregates"],
        "sales": data["sales"],
    }
