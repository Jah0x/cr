from typing import List

from pydantic import BaseModel, EmailStr, Field


class PlatformModuleResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None
    is_active: bool


class PlatformModuleCreate(BaseModel):
    code: str = Field(min_length=2)
    name: str = Field(min_length=2)
    description: str | None = None
    is_active: bool = True


class PlatformTemplateResponse(BaseModel):
    id: str
    name: str
    description: str | None
    module_codes: List[str]
    feature_codes: List[str]


class PlatformTemplateCreate(BaseModel):
    name: str = Field(min_length=2)
    description: str | None = None
    module_codes: List[str] = Field(default_factory=list)
    feature_codes: List[str] = Field(default_factory=list)


class PlatformTenantResponse(BaseModel):
    id: str
    name: str
    code: str
    status: str


class PlatformTenantCreate(BaseModel):
    name: str = Field(min_length=2)
    code: str = Field(min_length=2)
    template_id: str | None = None
    owner_email: EmailStr
    owner_password: str = Field(min_length=8)


class PlatformTenantCreateResponse(BaseModel):
    id: str
    name: str
    code: str
    status: str
    tenant_url: str
    owner_email: EmailStr
    owner_password: str
    owner_token: str


class PlatformTemplateApply(BaseModel):
    template_id: str
