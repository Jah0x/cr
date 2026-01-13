from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config

from app.core.config import settings


def _alembic_config(
    *,
    version_locations: Path,
    schema: str | None,
    version_table: str,
    version_table_schema: str | None,
) -> Config:
    alembic_ini_path = Path(settings.ALEMBIC_INI_PATH)
    script_location = alembic_ini_path.parent / "alembic"
    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(script_location))
    sync_url = make_sync_database_url(settings.database_url)
    config.set_main_option("sqlalchemy.url", sync_url)
    config.set_main_option("version_locations", str(version_locations))
    config.set_main_option("version_table", version_table)
    if schema:
        config.set_main_option("schema", schema)
    if version_table_schema:
        config.set_main_option("version_table_schema", version_table_schema)
    return config


def run_public_migrations() -> None:
    root = Path(settings.ALEMBIC_INI_PATH).parent
    public_versions = root / "alembic" / "versions" / "public"
    config = _alembic_config(
        version_locations=public_versions,
        schema="public",
        version_table="alembic_version",
        version_table_schema="public",
    )
    command.upgrade(config, "head")


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
    root = Path(settings.ALEMBIC_INI_PATH).parent
    tenant_versions = root / "alembic" / "versions" / "tenant"
    config = _alembic_config(
        version_locations=tenant_versions,
        schema=schema,
        version_table="alembic_version_tenant",
        version_table_schema=schema,
    )
    command.upgrade(config, "head")


def make_sync_database_url(async_url: str) -> str:
    """
    Alembic работает только с sync драйвером.
    Преобразует postgresql+asyncpg -> postgresql+psycopg
    """
    if "+asyncpg" in async_url:
        return async_url.replace("+asyncpg", "+psycopg")
    return async_url


def _sync_database_url() -> str:
    return make_sync_database_url(settings.database_url)


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
        root = Path(settings.ALEMBIC_INI_PATH).parent
        tenant_versions = root / "alembic" / "versions" / "tenant"
        config = _alembic_config(
            version_locations=tenant_versions,
            schema=schema,
            version_table=version_table,
            version_table_schema=schema,
        )
        command.stamp(config, "head")
