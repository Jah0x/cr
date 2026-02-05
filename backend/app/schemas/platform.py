from typing import List

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.tenancy import normalize_code, normalize_tenant_slug
from app.models.tenant import TenantStatus


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

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        return normalize_code(value)


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

    @field_validator("module_codes", "feature_codes")
    @classmethod
    def validate_codes(cls, values: List[str]) -> List[str]:
        return [normalize_code(value) for value in values]


class PlatformTenantResponse(BaseModel):
    id: str
    name: str
    code: str
    status: str
    last_error: str | None = None


class PlatformTenantCreate(BaseModel):
    name: str = Field(min_length=2)
    code: str = Field(min_length=2)
    template_id: str | None = None
    owner_email: EmailStr

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        return normalize_tenant_slug(value)


class PlatformTenantCreateResponse(BaseModel):
    id: str
    name: str
    code: str
    status: str
    tenant_url: str
    owner_email: EmailStr
    invite_url: str


class PlatformTenantStatusResponse(BaseModel):
    id: str
    name: str
    code: str
    status: str
    last_error: str | None = None
    schema: str
    schema_exists: bool
    revision: str | None
    head_revision: str | None


class PlatformTenantUpdate(BaseModel):
    name: str = Field(min_length=2)
    status: TenantStatus


class PlatformTenantUpdateResponse(BaseModel):
    id: str
    name: str
    code: str
    status: str
    last_error: str | None = None


class PlatformTenantDeleteResponse(BaseModel):
    id: str
    status: str
    schema_dropped: bool


class PlatformTenantDomainCreate(BaseModel):
    domain: str = Field(min_length=3)
    is_primary: bool = False


class PlatformTenantDomainResponse(BaseModel):
    id: str
    domain: str
    is_primary: bool
    created_at: str


class PlatformTenantInviteRequest(BaseModel):
    email: EmailStr
    role_name: str = Field(default="owner", min_length=2)


class PlatformTenantInviteResponse(BaseModel):
    invite_url: str
    expires_at: str


class PlatformTenantInviteItem(BaseModel):
    id: str
    email: EmailStr
    created_at: str
    expires_at: str
    used_at: str | None


class PlatformTenantUserResponse(BaseModel):
    id: str
    email: str
    roles: list[str]
    is_active: bool
    created_at: str
    last_login_at: str | None


class PlatformTenantUserCreate(BaseModel):
    email: EmailStr
    role_names: list[str]
    password: str | None = None
    invite: bool = False


class PlatformTenantUserUpdate(BaseModel):
    is_active: bool


class PlatformTemplateApply(BaseModel):
    template_id: str
