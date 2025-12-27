from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session, require_roles
from app.repos.user_repo import RoleRepo, UserRepo
from app.schemas.user import UserCreate, UserOut, UserRolesUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_roles({"owner"}))])


def get_service(session: AsyncSession):
    return UserService(UserRepo(session), RoleRepo(session))


@router.get("", response_model=list[UserOut])
async def list_users(session: AsyncSession = Depends(get_db_session)):
    users = await get_service(session).list_users()
    return users


@router.post("", response_model=UserOut)
async def create_user(payload: UserCreate, session: AsyncSession = Depends(get_db_session)):
    user = await get_service(session).create_user(payload.email, payload.password, payload.roles)
    return user


@router.post("/{user_id}/roles", response_model=UserOut)
async def set_roles(user_id: str, payload: UserRolesUpdate, session: AsyncSession = Depends(get_db_session)):
    user = await get_service(session).set_roles(user_id, payload.roles)
    return user
