from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import Module, TenantFeature, TenantModule, TenantUIPreference
from app.models.sales import PaymentProvider
from app.repos.tenant_settings_repo import TenantSettingsRepo


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

DEFAULT_TOBACCO_HIERARCHY_SETTINGS = {
    "catalog_hierarchy": {
        "levels": [
            {"code": "manufacturer", "title": "Производитель", "enabled": True},
            {"code": "model", "title": "Модель", "enabled": True},
            {"code": "flavor", "title": "Вкус", "enabled": True},
        ]
    }
}

DEFAULT_TAX_SETTINGS = {
    "enabled": False,
    "mode": "exclusive",
    "rounding": "round",
    "rules": [],
}

TAX_MODES = {"exclusive", "inclusive"}
TAX_ROUNDING = {"round", "ceil", "floor"}
TAX_METHODS = [method.value for method in PaymentProvider]


class TenantSettingsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tenant_settings_repo = TenantSettingsRepo(session)

    async def get_settings(self, tenant_id):
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
        tenant_settings = await self._load_tenant_settings(tenant_id)
        return {
            "modules": module_settings,
            "features": feature_settings,
            "ui_prefs": ui_prefs,
            "settings": tenant_settings,
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

    async def update_tenant_settings(self, tenant_id, patch: dict[str, Any]):
        if "settings" in patch and isinstance(patch["settings"], dict):
            patch = patch["settings"]
        settings_row = await self.tenant_settings_repo.get_or_create(tenant_id)
        current_settings = settings_row.settings or {}
        normalized_patch = self._normalize_settings(patch)
        merged = self._deep_merge(current_settings, normalized_patch)
        normalized = self._normalize_settings(merged)
        settings_row.settings = normalized
        settings_row.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return normalized

    async def _load_ui_prefs(self):
        current = await self.session.scalar(
            select(TenantUIPreference)
        )
        if not current:
            return DEFAULT_UI_PREFS.copy()
        return {**DEFAULT_UI_PREFS, **(current.prefs or {})}

    async def _load_tenant_settings(self, tenant_id):
        settings_row = await self.tenant_settings_repo.get_or_create(tenant_id)
        settings = settings_row.settings or {}
        normalized = self._normalize_settings(settings)
        if normalized != settings:
            settings_row.settings = normalized
            settings_row.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
        return normalized

    def _deep_merge(self, base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base)
        for key, value in patch.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _normalize_settings(self, settings: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(settings)
        nested_settings = normalized.pop("settings", None)
        if isinstance(nested_settings, dict):
            normalized = {**normalized, **nested_settings}
        if "taxes" in normalized:
            normalized["taxes"] = self._normalize_tax_settings(normalized.get("taxes"))
        return normalized

    def _normalize_tax_settings(self, raw: object) -> dict[str, Any]:
        if not isinstance(raw, dict):
            return DEFAULT_TAX_SETTINGS.copy()
        enabled = raw.get("enabled") if isinstance(raw.get("enabled"), bool) else DEFAULT_TAX_SETTINGS["enabled"]
        mode = raw.get("mode") if raw.get("mode") in TAX_MODES else DEFAULT_TAX_SETTINGS["mode"]
        rounding = raw.get("rounding") if raw.get("rounding") in TAX_ROUNDING else DEFAULT_TAX_SETTINGS["rounding"]
        rules_raw = raw.get("rules") if isinstance(raw.get("rules"), list) else []
        rules = []
        for index, rule in enumerate(rules_raw):
            if not isinstance(rule, dict):
                continue
            rule_id = rule.get("id")
            rule_name = rule.get("name")
            rate = rule.get("rate")
            is_active = rule.get("is_active")
            applies_to = rule.get("applies_to")
            if isinstance(rate, str):
                try:
                    rate = float(rate)
                except ValueError:
                    rate = 0
            if not isinstance(rate, (int, float)) or rate < 0:
                rate = 0
            normalized_methods = []
            if isinstance(applies_to, list):
                for method in applies_to:
                    if not isinstance(method, str):
                        continue
                    normalized_method = PaymentProvider.normalize(method)
                    if normalized_method in TAX_METHODS:
                        normalized_methods.append(normalized_method)
            if not normalized_methods:
                normalized_methods = TAX_METHODS.copy()
            rules.append(
                {
                    "id": str(rule_id) if rule_id else f"tax-{index}",
                    "name": str(rule_name) if isinstance(rule_name, str) else "",
                    "rate": rate,
                    "is_active": is_active if isinstance(is_active, bool) else True,
                    "applies_to": normalized_methods,
                }
            )
        return {
            "enabled": enabled,
            "mode": mode,
            "rounding": rounding,
            "rules": rules,
        }
