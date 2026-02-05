from datetime import datetime
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    get_current_tenant,
    get_current_user,
    get_db_session,
    require_module,
    require_roles,
)
from app.repos.finance_repo import (
    ExpenseAccrualRepo,
    ExpenseCategoryRepo,
    ExpenseRepo,
    RecurringExpenseRepo,
)
from app.repos.store_repo import StoreRepo
from app.schemas.finance import (
    ExpenseCategoryCreate,
    ExpenseCategoryOut,
    ExpenseCreate,
    ExpenseOut,
    RecurringExpenseCreate,
    RecurringExpenseOut,
    RecurringExpenseUpdate,
)
from app.services.finance_service import AccrualService, FinanceService

router = APIRouter(
    prefix="/finance",
    tags=["finance"],
    dependencies=[
        Depends(get_current_user),
        Depends(get_current_tenant),
        Depends(require_module("finance")),
    ],
)


def get_service(session: AsyncSession):
    recurring_repo = RecurringExpenseRepo(session)
    return FinanceService(
        ExpenseCategoryRepo(session),
        ExpenseRepo(session),
        recurring_repo,
        AccrualService(recurring_repo, ExpenseAccrualRepo(session)),
        StoreRepo(session),
    )


@router.get("/expense-categories", response_model=list[ExpenseCategoryOut])
async def list_categories(session: AsyncSession = Depends(get_db_session)):
    return await get_service(session).list_categories()


@router.post(
    "/expense-categories",
    response_model=ExpenseCategoryOut,
    dependencies=[Depends(require_roles({"owner", "admin"}))],
)
async def create_category(
    payload: ExpenseCategoryCreate, session: AsyncSession = Depends(get_db_session)
):
    return await get_service(session).create_category(payload.model_dump())


@router.get("/expenses", response_model=list[ExpenseOut])
async def list_expenses(
    store_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    return await get_service(session).list_expenses(store_id, date_from, date_to)


@router.post("/expenses", response_model=ExpenseOut)
async def create_expense(
    payload: ExpenseCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    return await get_service(session).create_expense(payload.model_dump(), current_user.id)


@router.delete(
    "/expenses/{expense_id}",
    dependencies=[Depends(require_roles({"owner", "admin"}))],
)
async def delete_expense(expense_id: str, session: AsyncSession = Depends(get_db_session)):
    await get_service(session).delete_expense(expense_id)
    return {"status": "ok"}


@router.post("/recurring-expenses", response_model=RecurringExpenseOut)
async def create_recurring_expense(
    payload: RecurringExpenseCreate,
    session: AsyncSession = Depends(get_db_session),
):
    return await get_service(session).create_recurring_expense(payload.model_dump())


@router.get("/recurring-expenses", response_model=list[RecurringExpenseOut])
async def list_recurring_expenses(
    store_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    return await get_service(session).list_recurring_expenses(store_id)


@router.put("/recurring-expenses/{recurring_expense_id}", response_model=RecurringExpenseOut)
async def update_recurring_expense(
    recurring_expense_id: uuid.UUID,
    payload: RecurringExpenseUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    return await get_service(session).update_recurring_expense(
        recurring_expense_id, payload.model_dump()
    )


@router.delete("/recurring-expenses/{recurring_expense_id}", response_model=RecurringExpenseOut)
async def delete_recurring_expense(
    recurring_expense_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
):
    return await get_service(session).delete_recurring_expense(recurring_expense_id)
