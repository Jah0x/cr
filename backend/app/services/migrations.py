from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from fastapi import HTTPException, status

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.config import get_settings
from app.core.db_utils import quote_ident
from app.core.tenancy import normalize_tenant_slug
from app.models.tenant import TenantStatus

logger = logging.getLogger(__name__)
from app.core.db_urls import normalize_migration_database_url


def _alembic_config(
    *,
    version_locations: list[Path],
    schema: str | None,
    version_table: str,
    version_table_schema: str | None,
) -> Config:
    settings = get_settings()
    alembic_ini_path = Path(settings.ALEMBIC_INI_PATH)
    script_location = alembic_ini_path.parent / "alembic"
    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(script_location))
    sync_url = normalize_migration_database_url(settings.database_url)
    config.set_main_option("sqlalchemy.url", sync_url)
    config.set_main_option(
        "version_locations",
        " ".join(str(path) for path in version_locations),
    )
    config.set_main_option("version_table", version_table)
    if schema:
        config.set_main_option("schema", schema)
    if version_table_schema:
        config.set_main_option("version_table_schema", version_table_schema)
    return config


def _tenant_script_directory() -> ScriptDirectory:
    settings = get_settings()
    root = Path(settings.ALEMBIC_INI_PATH).parent
    script_location = root / "alembic"
    public_versions = script_location / "versions" / "public"
    tenant_versions = script_location / "versions" / "tenant"
    config = _alembic_config(
        version_locations=[public_versions, tenant_versions],
        schema=None,
        version_table="alembic_version_tenant",
        version_table_schema=None,
    )
    return ScriptDirectory.from_config(config)


def get_tenant_head_revision() -> str | None:
    script = _tenant_script_directory()
    revisions = script.get_revisions("tenant@head")
    if not revisions:
        return None
    return revisions[0].revision


def get_tenant_migration_status(schema: str) -> dict:
    schema = normalize_tenant_slug(schema)
    engine = create_engine(_sync_database_url())
    head_revision = get_tenant_head_revision()
    with engine.connect() as conn:
        schema_exists = conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.schemata
                    WHERE schema_name = :schema
                )
                """
            ),
            {"schema": schema},
        ).scalar()
        revision = None
        if schema_exists:
            version_table = conn.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = :schema
                          AND table_name = 'alembic_version_tenant'
                    )
                    """
                ),
                {"schema": schema},
            ).scalar()
            if version_table:
                safe_schema = quote_ident(schema)
                revision = conn.execute(
                    text(f"SELECT version_num FROM {safe_schema}.alembic_version_tenant LIMIT 1")
                ).scalar()
    engine.dispose()
    return {
        "schema": schema,
        "schema_exists": bool(schema_exists),
        "revision": revision,
        "head_revision": head_revision,
    }


async def ensure_tenant_ready(session, tenant, *, correlation_id: str | None = None) -> None:
    schema = normalize_tenant_slug(tenant.code)
    status_info = get_tenant_migration_status(schema)
    if not status_info["schema_exists"]:
        detail = f"Tenant schema '{schema}' is missing"
        logger.error("Tenant schema missing: schema=%s correlation_id=%s", schema, correlation_id)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
    head_revision = status_info["head_revision"]
    current_revision = status_info["revision"]
    if head_revision and current_revision != head_revision:
        logger.info(
            "Tenant schema %s not at head (current=%s head=%s) correlation_id=%s",
            schema,
            current_revision,
            head_revision,
            correlation_id,
        )
        auto_migrate = os.getenv("ENABLE_AUTO_MIGRATIONS", "").lower() in {"1", "true", "yes", "on"}
        if not auto_migrate:
            detail = (
                f"Tenant schema '{schema}' is not migrated. "
                "Run tenant migrations with the migration CLI or enable auto migrations."
            )
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
        try:
            await asyncio.to_thread(run_tenant_migrations, schema)
            tenant.status = TenantStatus.active
            tenant.last_error = None
            await session.flush()
        except Exception as exc:
            tenant.status = TenantStatus.provisioning_failed
            tenant.last_error = str(exc)
            await session.flush()
            logger.exception(
                "Tenant migrations failed for schema=%s correlation_id=%s",
                schema,
                correlation_id,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Tenant migrations failed: {exc}",
            ) from exc


def run_public_migrations() -> None:
    settings = get_settings()
    root = Path(settings.ALEMBIC_INI_PATH).parent
    public_versions = root / "alembic" / "versions" / "public"
    tenant_versions = root / "alembic" / "versions" / "tenant"
    config = _alembic_config(
        version_locations=[public_versions, tenant_versions],
        schema="public",
        version_table="alembic_version",
        version_table_schema="public",
    )
    command.upgrade(config, "public@head")


async def verify_public_migrations(engine) -> None:
    async with engine.connect() as conn:
        res = await conn.execute(
            text(
                """
                select
                    to_regclass('public.alembic_version') as alembic,
                    to_regclass('public.modules') as modules,
                    exists(
                        select 1
                        from information_schema.tables
                        where table_schema = 'public'
                          and table_name = 'alembic_version'
                    ) as alembic_exists,
                    exists(
                        select 1
                        from information_schema.tables
                        where table_schema = 'public'
                          and table_name = 'modules'
                    ) as modules_exists
                """
            )
        )
        row = res.mappings().first()

    alembic_ok = row and (row["alembic"] or row["alembic_exists"])
    modules_ok = row and (row["modules"] or row["modules_exists"])
    if not alembic_ok or not modules_ok:
        raise RuntimeError(f"Alembic migration failed: tables not created: {row}")


def run_tenant_migrations(schema: str) -> None:
    _ensure_tenant_version_table(schema)
    settings = get_settings()
    root = Path(settings.ALEMBIC_INI_PATH).parent
    public_versions = root / "alembic" / "versions" / "public"
    tenant_versions = root / "alembic" / "versions" / "tenant"
    config = _alembic_config(
        version_locations=[public_versions, tenant_versions],
        schema=schema,
        version_table="alembic_version_tenant",
        version_table_schema=schema,
    )
    command.upgrade(config, "tenant@head")


def _sync_database_url() -> str:
    settings = get_settings()
    return normalize_migration_database_url(settings.database_url)


def _ensure_tenant_version_table(schema: str) -> None:
    engine = create_engine(_sync_database_url())
    version_table = "alembic_version_tenant"
    with engine.connect() as conn:
        has_version_table = conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = :schema
                      AND table_name = :table_name
                )
                """
            ),
            {"schema": schema, "table_name": version_table},
        ).scalar()
        has_tables = conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = :schema
                      AND table_name != :table_name
                )
                """
            ),
            {"schema": schema, "table_name": version_table},
        ).scalar()
    engine.dispose()
    if has_tables and not has_version_table:
        settings = get_settings()
        root = Path(settings.ALEMBIC_INI_PATH).parent
        public_versions = root / "alembic" / "versions" / "public"
        tenant_versions = root / "alembic" / "versions" / "tenant"
        config = _alembic_config(
            version_locations=[public_versions, tenant_versions],
            schema=schema,
            version_table=version_table,
            version_table_schema=schema,
        )
        command.stamp(config, "tenant@head")
