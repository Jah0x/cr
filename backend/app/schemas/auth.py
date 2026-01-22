from pydantic import BaseModel, EmailStr, Field


class InviteInfoResponse(BaseModel):
    email: EmailStr
    tenant_code: str


class InviteRegisterPayload(BaseModel):
    token: str = Field(min_length=10)
    password: str = Field(min_length=8)
