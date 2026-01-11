from __future__ import annotations

from pathlib import Path

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
    config.set_main_option("sqlalchemy.url", settings.database_url)
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


def run_tenant_migrations(schema: str) -> None:
    config = _alembic_config(
        version_locations=TENANT_VERSIONS,
        schema=schema,
        version_table="alembic_version",
        version_table_schema="public",
    )
    command.upgrade(config, "head")
