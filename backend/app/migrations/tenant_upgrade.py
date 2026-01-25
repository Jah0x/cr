import argparse
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

from app.core.tenancy import normalize_tenant_slug


def _normalize_alembic_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if database_url.startswith("postgres+asyncpg://"):
        return database_url.replace("postgres+asyncpg://", "postgres://", 1)
    return database_url


def _build_alembic_config(base_dir: Path, database_url: str, schema: str) -> Config:
    alembic_ini_path = base_dir / "alembic.ini"
    script_location = base_dir / "alembic"
    public_versions = script_location / "versions" / "public"
    tenant_versions = script_location / "versions" / "tenant"
    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(script_location))
    config.set_main_option("sqlalchemy.url", database_url)
    config.set_main_option("version_locations", f"{public_versions} {tenant_versions}")
    config.set_main_option("schema", schema)
    config.set_main_option("version_table", "alembic_version_tenant")
    config.set_main_option("version_table_schema", schema)
    return config


def _resolve_database_url() -> str:
    database_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_DSN")
    if not database_url:
        raise RuntimeError("DATABASE_URL or DATABASE_DSN is required to run migrations.")
    return _normalize_alembic_database_url(database_url)


def _resolve_revision(revision: str) -> str:
    if "@" in revision:
        return revision
    return f"tenant@{revision}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run tenant alembic migrations.")
    parser.add_argument("--schema", default=os.getenv("TENANT_SCHEMA", "public"))
    parser.add_argument("--revision", default="head")
    args = parser.parse_args()

    try:
        schema = normalize_tenant_slug(args.schema)
    except ValueError as exc:
        sys.stderr.write(f"Invalid tenant schema: {exc}\n")
        sys.exit(1)

    try:
        database_url = _resolve_database_url()
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
        sys.exit(1)

    base_dir = Path(__file__).resolve().parents[2]
    config = _build_alembic_config(base_dir, database_url, schema)
    revision = _resolve_revision(args.revision)

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            quoted_schema = connection.dialect.identifier_preparer.quote(schema)
            connection.exec_driver_sql(f"CREATE SCHEMA IF NOT EXISTS {quoted_schema}")
            if schema == "public":
                connection.exec_driver_sql("SET search_path TO public")
            else:
                connection.exec_driver_sql(f"SET search_path TO {quoted_schema}, public")
            config.attributes["connection"] = connection
            command.upgrade(config, revision)
            connection.commit()
    except Exception as exc:
        sys.stderr.write(f"Tenant migration failed: {exc}\n")
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
