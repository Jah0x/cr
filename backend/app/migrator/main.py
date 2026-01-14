import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config


def _normalize_database_url(database_url: str) -> str:
    if "+" not in database_url and database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


def _make_sync_database_url(async_url: str) -> str:
    if "+asyncpg" in async_url:
        return async_url.replace("+asyncpg", "+psycopg")
    return async_url


def _build_alembic_config(base_dir: Path, database_url: str) -> Config:
    alembic_ini_path = base_dir / "alembic.ini"
    script_location = base_dir / "migrator_alembic"
    public_versions = base_dir / "alembic" / "versions" / "public"
    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(script_location))
    config.set_main_option("sqlalchemy.url", _make_sync_database_url(database_url))
    config.set_main_option("version_locations", str(public_versions))
    config.set_main_option("version_table", "alembic_version")
    config.set_main_option("schema", "public")
    config.set_main_option("version_table_schema", "public")
    return config


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        sys.stderr.write("DATABASE_URL is required to run migrations.\n")
        sys.exit(1)

    base_dir = Path(__file__).resolve().parents[2]
    config = _build_alembic_config(base_dir, _normalize_database_url(database_url))

    try:
        command.upgrade(config, "head")
    except Exception as exc:
        sys.stderr.write(f"Migration failed: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
