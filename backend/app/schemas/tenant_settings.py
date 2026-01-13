from typing import Any, Dict, List

from pydantic import BaseModel, Field


class TenantModuleSetting(BaseModel):
    code: str
    name: str
    description: str | None
    is_active: bool
    is_enabled: bool


class TenantFeatureSetting(BaseModel):
    code: str
    name: str
    description: str | None
    is_enabled: bool


class TenantUIPrefs(BaseModel):
    prefs: Dict[str, bool] = Field(default_factory=dict)


class TenantSettingsResponse(BaseModel):
    modules: List[TenantModuleSetting]
    features: List[TenantFeatureSetting]
    ui_prefs: Dict[str, bool]
    settings: Dict[str, Any]


class TenantModuleUpdate(BaseModel):
    is_enabled: bool


class TenantFeatureUpdate(BaseModel):
    is_enabled: bool


class TenantUIPrefsUpdate(BaseModel):
    prefs: Dict[str, bool]


class TenantSettingsPayload(BaseModel):
    settings: Dict[str, Any]
