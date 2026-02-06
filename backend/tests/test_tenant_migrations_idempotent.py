from __future__ import annotations

import os
import pathlib
import sys

import pytest
from sqlalchemy import create_engine, text

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

os.environ.setdefault("JWT_SECRET", "test")

from app.core.db_urls import normalize_migration_database_url
from app.core.db_utils import quote_ident
from app.services.migrations import (
    DEFAULT_VERSION_TABLE,
    get_tenant_head_revision,
    get_tenant_migration_status,
    run_tenant_migrations,
)


def _require_postgres_url() -> str:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        pytest.skip("DATABASE_URL is not set; requires Postgres for tenant migration test.")
    if database_url.startswith("sqlite"):
        pytest.skip("SQLite does not support tenant schemas; requires Postgres.")
    if not database_url.startswith(("postgres://", "postgresql://", "postgresql+")):
        pytest.skip("DATABASE_URL is not a Postgres URL; requires Postgres.")
    return database_url


def test_tenant_migrations_idempotent() -> None:
    database_url = _require_postgres_url()
    schema = "qa_tenant_schema"
    engine = create_engine(normalize_migration_database_url(database_url))
    quoted_schema = quote_ident(schema)

    with engine.connect() as conn:
        conn.exec_driver_sql(f"DROP SCHEMA IF EXISTS {quoted_schema} CASCADE")
        conn.exec_driver_sql(f"CREATE SCHEMA {quoted_schema}")
        conn.commit()

    try:
        run_tenant_migrations(schema)
        run_tenant_migrations(schema)

        status = get_tenant_migration_status(schema)
        assert status["schema_exists"] is True
        assert status["version_table"] == DEFAULT_VERSION_TABLE
        assert status["revision"] == get_tenant_head_revision()

        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT
                        to_regclass(:alembic) as alembic,
                        to_regclass(:categories) as categories,
                        to_regclass(:products) as products
                    """
                ),
                {
                    "alembic": f"{schema}.{DEFAULT_VERSION_TABLE}",
                    "categories": f"{schema}.categories",
                    "products": f"{schema}.products",
                },
            ).mappings().one()
        assert result["alembic"]
        assert result["categories"]
        assert result["products"]
    finally:
        with engine.connect() as conn:
            conn.exec_driver_sql(f"DROP SCHEMA IF EXISTS {quoted_schema} CASCADE")
            conn.commit()
        engine.dispose()
