from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import Module, TenantFeature, TenantModule, TenantUIPreference


AVAILABLE_FEATURES = [
    {
        "code": "reports",
        "name": "Reports",
        "description": "Access reporting endpoints.",
    },
    {
        "code": "ui_prefs",
        "name": "UI preferences",
        "description": "Customize the tenant UI preferences.",
    },
]

DEFAULT_UI_PREFS = {
    "compact_nav": False,
    "show_help": True,
}


class TenantSettingsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_settings(self):
        modules = await self.session.execute(select(Module))
        modules = modules.scalars().all()
        tenant_modules = await self.session.execute(select(TenantModule))
        tenant_module_map = {item.module_id: item for item in tenant_modules.scalars()}
        module_settings = []
        for module in modules:
            tenant_module = tenant_module_map.get(module.id)
            is_enabled = tenant_module.is_enabled if tenant_module else False
            module_settings.append(
                {
                    "code": module.code,
                    "name": module.name,
                    "description": module.description,
                    "is_active": module.is_active,
                    "is_enabled": is_enabled,
                }
            )

        tenant_features = await self.session.execute(select(TenantFeature))
        feature_map = {item.code: item for item in tenant_features.scalars()}
        feature_settings = []
        for feature in AVAILABLE_FEATURES:
            stored = feature_map.get(feature["code"])
            is_enabled = stored.is_enabled if stored else False
            feature_settings.append(
                {
                    "code": feature["code"],
                    "name": feature["name"],
                    "description": feature["description"],
                    "is_enabled": is_enabled,
                }
            )

        ui_prefs = await self._load_ui_prefs()
        return {
            "modules": module_settings,
            "features": feature_settings,
            "ui_prefs": ui_prefs,
        }

    def _build_module_setting(self, module: Module, is_enabled: bool):
        return {
            "code": module.code,
            "name": module.name,
            "description": module.description,
            "is_active": module.is_active,
            "is_enabled": is_enabled,
        }

    def _build_feature_setting(self, feature: dict, is_enabled: bool):
        return {
            "code": feature["code"],
            "name": feature["name"],
            "description": feature["description"],
            "is_enabled": is_enabled,
        }

    async def update_module(self, code: str, is_enabled: bool):
        module = await self.session.scalar(select(Module).where(Module.code == code))
        if not module:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
        if is_enabled and not module.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Module is inactive")
        tenant_module = await self.session.scalar(
            select(TenantModule).where(TenantModule.module_id == module.id)
        )
        if tenant_module:
            tenant_module.is_enabled = is_enabled
        else:
            tenant_module = TenantModule(
                module_id=module.id,
                is_enabled=is_enabled,
            )
            self.session.add(tenant_module)
        return self._build_module_setting(module, tenant_module.is_enabled)

    async def delete_module(self, code: str):
        module = await self.session.scalar(select(Module).where(Module.code == code))
        if not module:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
        tenant_module = await self.session.scalar(
            select(TenantModule).where(TenantModule.module_id == module.id)
        )
        if tenant_module:
            await self.session.delete(tenant_module)
        return self._build_module_setting(module, False)

    async def update_feature(self, code: str, is_enabled: bool):
        feature = next((item for item in AVAILABLE_FEATURES if item["code"] == code), None)
        if not feature:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature not found")
        tenant_feature = await self.session.scalar(
            select(TenantFeature).where(TenantFeature.code == code)
        )
        if tenant_feature:
            tenant_feature.is_enabled = is_enabled
        else:
            tenant_feature = TenantFeature(
                code=code,
                is_enabled=is_enabled,
            )
            self.session.add(tenant_feature)
        return self._build_feature_setting(feature, tenant_feature.is_enabled)

    async def delete_feature(self, code: str):
        feature = next((item for item in AVAILABLE_FEATURES if item["code"] == code), None)
        if not feature:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature not found")
        tenant_feature = await self.session.scalar(
            select(TenantFeature).where(TenantFeature.code == code)
        )
        if tenant_feature:
            await self.session.delete(tenant_feature)
        return self._build_feature_setting(feature, False)

    async def update_ui_prefs(self, prefs: dict[str, bool]):
        current = await self.session.scalar(
            select(TenantUIPreference)
        )
        merged = {**DEFAULT_UI_PREFS, **(current.prefs if current else {}), **prefs}
        if current:
            current.prefs = merged
            current.updated_at = datetime.now(timezone.utc)
        else:
            current = TenantUIPreference(
                prefs=merged,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.session.add(current)
        return merged

    async def delete_ui_prefs(self):
        current = await self.session.scalar(
            select(TenantUIPreference)
        )
        if current:
            await self.session.delete(current)
        return DEFAULT_UI_PREFS.copy()

    async def _load_ui_prefs(self):
        current = await self.session.scalar(
            select(TenantUIPreference)
        )
        if not current:
            return DEFAULT_UI_PREFS.copy()
        return {**DEFAULT_UI_PREFS, **(current.prefs or {})}
