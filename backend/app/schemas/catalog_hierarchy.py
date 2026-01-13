import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field


class CatalogHierarchyLevel(BaseModel):
    code: str
    title: Optional[str] = None
    enabled: bool = True


class CatalogNodeBase(BaseModel):
    level_code: str
    parent_id: Optional[uuid.UUID] = None
    name: str
    code: Optional[str] = None
    meta: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class CatalogNodeCreate(CatalogNodeBase):
    pass


class CatalogNodeUpdate(BaseModel):
    level_code: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    code: Optional[str] = None
    meta: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class CatalogNodeOut(CatalogNodeBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}


class CatalogHierarchyResponse(BaseModel):
    levels: list[CatalogHierarchyLevel]
    roots: list[CatalogNodeOut]
