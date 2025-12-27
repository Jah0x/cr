import uuid
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    roles: list[str]


class RoleOut(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    tenant_id: uuid.UUID
    roles: list[RoleOut]

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


class UserRolesUpdate(BaseModel):
    roles: list[str]
