from pydantic import BaseModel, EmailStr, Field


class InvitationCreateRequest(BaseModel):
    email: EmailStr
    role_name: str = Field(default="owner", min_length=2)


class InvitationCreateResponse(BaseModel):
    invite_url: str
    expires_at: str


class InvitationDetailResponse(BaseModel):
    email: EmailStr
    tenant_code: str


class InvitationAcceptRequest(BaseModel):
    password: str = Field(min_length=8)
