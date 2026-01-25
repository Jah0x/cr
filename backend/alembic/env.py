import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import models
from app.core.db import Base
from app.core.tenancy import normalize_tenant_slug

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_DSN")
    if not url:
        raise RuntimeError("DATABASE_URL or DATABASE_DSN is required to run migrations.")
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("postgres+asyncpg://"):
        return url.replace("postgres+asyncpg://", "postgres://", 1)
    return url


def _get_tenant_schema() -> str:
    schema = os.getenv("TENANT_SCHEMA") or config.get_main_option("schema", "public")
    return normalize_tenant_slug(schema)


def run_migrations_offline() -> None:
    schema = _get_tenant_schema()
    version_table = config.get_main_option("version_table", "alembic_version")
    version_table_schema = config.get_main_option("version_table_schema", schema)
    configure_opts = {
        "url": _get_database_url(),
        "target_metadata": target_metadata,
        "literal_binds": True,
        "compare_type": True,
        "compare_server_default": True,
        "dialect_opts": {"paramstyle": "named"},
        "version_table": version_table,
        "version_table_schema": version_table_schema,
        "include_schemas": True,
    }

    context.configure(**configure_opts)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    database_url = _get_database_url()
    config.set_main_option("sqlalchemy.url", database_url)
    schema = _get_tenant_schema()
    version_table = config.get_main_option("version_table", "alembic_version")
    version_table_schema = config.get_main_option("version_table_schema", schema)
    external_connection = config.attributes.get("connection")
    if external_connection is not None:
        connection = external_connection
        connectable = None
    else:
        configuration = config.get_section(config.config_ini_section) or {}
        configuration["sqlalchemy.url"] = database_url
        connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
        connection = connectable.connect()

    try:
        quoted_schema = connection.dialect.identifier_preparer.quote(schema)
        connection.exec_driver_sql(f"CREATE SCHEMA IF NOT EXISTS {quoted_schema}")
        if schema == "public":
            connection.exec_driver_sql("SET search_path TO public")
        else:
            connection.exec_driver_sql(f"SET search_path TO {quoted_schema}, public")
        configure_opts = {
            "connection": connection,
            "target_metadata": target_metadata,
            "compare_type": True,
            "compare_server_default": True,
            "version_table": version_table,
            "version_table_schema": version_table_schema,
            "include_schemas": True,
        }

        context.configure(**configure_opts)

        with context.begin_transaction():
            context.run_migrations()
    finally:
        if connectable is not None:
            connection.close()
            connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
