import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.db_urls import normalize_migration_database_url


def _build_alembic_config(base_dir: Path, database_url: str) -> Config:
    alembic_ini_path = base_dir / "alembic.ini"
    script_location = base_dir / "alembic"
    public_versions = script_location / "versions" / "public"
    tenant_versions = script_location / "versions" / "tenant"
    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(script_location))
    config.set_main_option("sqlalchemy.url", normalize_migration_database_url(database_url))
    config.set_main_option("version_locations", f"{public_versions} {tenant_versions}")
    config.set_main_option("version_table", "alembic_version")
    config.set_main_option("schema", "public")
    config.set_main_option("version_table_schema", "public")
    return config


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        sys.stderr.write("DATABASE_URL is required to run migrations.\n")
        sys.exit(1)

    base_dir = Path(__file__).resolve().parents[1]
    config = _build_alembic_config(base_dir, normalize_migration_database_url(database_url))

    try:
        command.upgrade(config, "public@head")
    except Exception as exc:
        sys.stderr.write(f"Migration failed: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
