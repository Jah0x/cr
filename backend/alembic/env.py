import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import models
from app.core.db import Base
from app.core.db_urls import normalize_migration_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_option(name: str, default: str | None = None) -> str | None:
    value = config.get_main_option(name)
    if value:
        return value
    return default


def _quote_identifier(value: str) -> str:
    escaped = value.replace('"', '""')
    return f'"{escaped}"'


def _get_database_url() -> str:
    url = _get_option("sqlalchemy.url") or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required to run migrations.")
    return normalize_migration_database_url(url)


def run_migrations_offline() -> None:
    schema = _get_option("schema")
    configure_opts = {
        "url": _get_database_url(),
        "target_metadata": target_metadata,
        "literal_binds": True,
        "compare_type": True,
        "compare_server_default": True,
        "dialect_opts": {"paramstyle": "named"},
        "version_table": _get_option("version_table", "alembic_version"),
    }
    version_table_schema = _get_option("version_table_schema")
    if version_table_schema:
        configure_opts["version_table_schema"] = version_table_schema
    if schema:
        configure_opts["include_schemas"] = True

    context.configure(**configure_opts)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    schema = _get_option("schema")
    connectable = create_engine(_get_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        if schema:
            connection.exec_driver_sql(f"SET search_path TO {_quote_identifier(schema)}")
        configure_opts = {
            "connection": connection,
            "target_metadata": target_metadata,
            "compare_type": True,
            "compare_server_default": True,
            "version_table": _get_option("version_table", "alembic_version"),
        }
        version_table_schema = _get_option("version_table_schema")
        if version_table_schema:
            configure_opts["version_table_schema"] = version_table_schema
        if schema:
            configure_opts["include_schemas"] = True

        context.configure(**configure_opts)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
