from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config

from app.core.config import settings


BASE_DIR = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = BASE_DIR / "alembic.ini"
SCRIPT_LOCATION = BASE_DIR / "alembic"
PUBLIC_VERSIONS = SCRIPT_LOCATION / "versions" / "public"
TENANT_VERSIONS = SCRIPT_LOCATION / "versions" / "tenant"


def _alembic_config(
    *,
    version_locations: Path,
    schema: str | None,
    version_table: str,
    version_table_schema: str | None,
) -> Config:
    config = Config(str(ALEMBIC_INI_PATH))
    config.set_main_option("script_location", str(SCRIPT_LOCATION))
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
    config = _alembic_config(
        version_locations=PUBLIC_VERSIONS,
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
                    to_regclass('public.modules') as modules
                """
            )
        )
        row = res.mappings().first()

    if not row or not row["alembic"] or not row["modules"]:
        raise RuntimeError(f"Alembic migration failed: tables not created: {row}")


def run_tenant_migrations(schema: str) -> None:
    _ensure_tenant_version_table(schema)
    config = _alembic_config(
        version_locations=TENANT_VERSIONS,
        schema=schema,
        version_table="alembic_version",
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
    version_table = "alembic_version"
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
        config = _alembic_config(
            version_locations=TENANT_VERSIONS,
            schema=schema,
            version_table=version_table,
            version_table_schema=schema,
        )
        command.stamp(config, "head")
