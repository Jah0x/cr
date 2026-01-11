from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_utils import set_search_path
from app.models.platform import Module, TenantFeature, TenantModule


async def apply_template_codes(
    session: AsyncSession,
    *,
    schema: str,
    module_codes: list[str] | None,
    feature_codes: list[str] | None,
    validate_modules: bool = False,
) -> list[str]:
    await set_search_path(session, schema)
    module_codes = list(dict.fromkeys(module_codes or []))
    feature_codes = list(dict.fromkeys(feature_codes or []))
    missing: list[str] = []
    if module_codes:
        modules = await session.execute(select(Module).where(Module.code.in_(module_codes)))
        module_map = {module.code: module for module in modules.scalars()}
        missing = [code for code in module_codes if code not in module_map]
        if validate_modules and missing:
            return missing
        existing_modules = await session.execute(select(TenantModule))
        existing_map = {row.module_id: row for row in existing_modules.scalars()}
        for module in module_map.values():
            existing = existing_map.get(module.id)
            if existing:
                existing.is_enabled = True
                continue
            session.add(
                TenantModule(
                    module_id=module.id,
                    is_enabled=True,
                    created_at=datetime.now(timezone.utc),
                )
            )
    if feature_codes:
        existing_features = await session.execute(select(TenantFeature))
        existing_map = {row.code: row for row in existing_features.scalars()}
        for code in feature_codes:
            existing = existing_map.get(code)
            if existing:
                existing.is_enabled = True
                continue
            session.add(
                TenantFeature(
                    code=code,
                    is_enabled=True,
                    created_at=datetime.now(timezone.utc),
                )
            )
    return missing
