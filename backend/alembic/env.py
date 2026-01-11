import asyncio
import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings
from app.core.db import Base
from app import models

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

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


def run_migrations_offline() -> None:
    schema = _get_option("schema")
    configure_opts = {
        "url": settings.database_url,
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


def do_run_migrations(connection: Connection) -> None:
    schema = _get_option("schema")
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


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = settings.database_url
    connectable = async_engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

        await connectable.dispose()

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
