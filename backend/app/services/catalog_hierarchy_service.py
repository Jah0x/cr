from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.repos.catalog_nodes_repo import CatalogNodeRepo
from app.repos.tenant_settings_repo import TenantSettingsRepo


class CatalogHierarchyService:
    def __init__(self, node_repo: CatalogNodeRepo, tenant_settings_repo: TenantSettingsRepo):
        self.node_repo = node_repo
        self.tenant_settings_repo = tenant_settings_repo
        self.session = node_repo.session

    async def get_hierarchy(self, tenant_id):
        settings_row = await self.tenant_settings_repo.get_or_create(tenant_id)
        settings = settings_row.settings or {}
        levels = []
        for level in settings.get("catalog_hierarchy", {}).get("levels", []):
            if isinstance(level, dict) and level.get("enabled", True):
                levels.append(level)
        roots = await self.node_repo.list(parent_id=None, filter_parent=True)
        return {"levels": levels, "roots": roots}

    async def list_nodes(self, parent_id=None, level_code: str | None = None):
        return await self.node_repo.list(parent_id=parent_id, level_code=level_code, filter_parent=parent_id is not None)

    async def create_node(self, data: dict[str, Any]):
        parent_id = data.get("parent_id")
        if parent_id is not None:
            parent = await self.node_repo.get(parent_id)
            if not parent:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent node not found")
        node = await self.node_repo.create(data)
        await self.session.refresh(node)
        return node

    async def update_node(self, node_id, data: dict[str, Any]):
        node = await self.node_repo.get(node_id)
        if not node:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
        if "parent_id" in data and data["parent_id"] is not None:
            parent = await self.node_repo.get(data["parent_id"])
            if not parent:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent node not found")
        for key, value in data.items():
            if value is not None:
                setattr(node, key, value)
        await self.session.flush()
        await self.session.refresh(node)
        return node

    async def delete_node(self, node_id):
        node = await self.node_repo.get(node_id)
        if not node:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
        node.is_active = False
        await self.session.flush()
