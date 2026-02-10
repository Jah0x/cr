from __future__ import annotations

import os
import pathlib
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, text

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

os.environ.setdefault("JWT_SECRET", "test")

from app.core.config import get_settings
from app.core.db_urls import normalize_migration_database_url
from app.core.db_utils import quote_ident
from app.services.migrations import (
    TenantMigrationLockTimeoutError,
    _advisory_lock_key,
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


def _reset_settings_cache() -> None:
    get_settings.cache_clear()


def test_tenant_migration_lock_timeout_when_busy(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = _require_postgres_url()
    schema = "qa_tenant_lock_schema"
    engine = create_engine(normalize_migration_database_url(database_url))
    quoted_schema = quote_ident(schema)

    with engine.connect() as conn:
        conn.exec_driver_sql(f"DROP SCHEMA IF EXISTS {quoted_schema} CASCADE")
        conn.exec_driver_sql(f"CREATE SCHEMA {quoted_schema}")
        conn.commit()

    lock_key = _advisory_lock_key(schema)
    try:
        with engine.connect() as conn:
            acquired = conn.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": lock_key}).scalar()
            assert acquired
            monkeypatch.setenv("TENANT_MIGRATION_LOCK_TIMEOUT", "1")
            monkeypatch.setenv("ENABLE_WAIT_FOR_MIGRATION_LOCK", "false")
            _reset_settings_cache()
            with pytest.raises(TenantMigrationLockTimeoutError):
                run_tenant_migrations(schema, correlation_id="test-lock-timeout")
            conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": lock_key})
            conn.commit()

        monkeypatch.setenv("ENABLE_WAIT_FOR_MIGRATION_LOCK", "true")
        _reset_settings_cache()
        run_tenant_migrations(schema, correlation_id="test-lock-success")
    finally:
        with engine.connect() as conn:
            conn.exec_driver_sql(f"DROP SCHEMA IF EXISTS {quoted_schema} CASCADE")
            conn.commit()
        engine.dispose()


def test_tenant_migration_requires_force_stamp(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = _require_postgres_url()
    schema = "qa_tenant_stamp_schema"
    engine = create_engine(normalize_migration_database_url(database_url))
    quoted_schema = quote_ident(schema)

    with engine.connect() as conn:
        conn.exec_driver_sql(f"DROP SCHEMA IF EXISTS {quoted_schema} CASCADE")
        conn.exec_driver_sql(f"CREATE SCHEMA {quoted_schema}")
        conn.exec_driver_sql(f"CREATE TABLE {quoted_schema}.categories (id uuid primary key)")
        conn.exec_driver_sql(f"CREATE TABLE {quoted_schema}.products (id uuid primary key)")
        conn.commit()

    try:
        monkeypatch.setenv("FORCE_STAMP_IF_TABLES_EXIST", "false")
        _reset_settings_cache()
        with pytest.raises(RuntimeError):
            run_tenant_migrations(schema, correlation_id="test-stamp-required")

        monkeypatch.setenv("FORCE_STAMP_IF_TABLES_EXIST", "true")
        _reset_settings_cache()
        run_tenant_migrations(schema, correlation_id="test-stamp-forced")
    finally:
        with engine.connect() as conn:
            conn.exec_driver_sql(f"DROP SCHEMA IF EXISTS {quoted_schema} CASCADE")
            conn.commit()
        engine.dispose()


def test_parallel_tenant_migrations_serialize(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = _require_postgres_url()
    schema = "qa_tenant_parallel_schema"
    engine = create_engine(normalize_migration_database_url(database_url))
    quoted_schema = quote_ident(schema)

    with engine.connect() as conn:
        conn.exec_driver_sql(f"DROP SCHEMA IF EXISTS {quoted_schema} CASCADE")
        conn.exec_driver_sql(f"CREATE SCHEMA {quoted_schema}")
        conn.commit()

    barrier = threading.Barrier(2)
    monkeypatch.setenv("ENABLE_WAIT_FOR_MIGRATION_LOCK", "true")
    monkeypatch.setenv("TENANT_MIGRATION_LOCK_TIMEOUT", "30")
    _reset_settings_cache()

    def _run() -> None:
        barrier.wait(timeout=10)
        run_tenant_migrations(schema, correlation_id="test-parallel")

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(_run) for _ in range(2)]
            for future in futures:
                future.result()
    finally:
        with engine.connect() as conn:
            conn.exec_driver_sql(f"DROP SCHEMA IF EXISTS {quoted_schema} CASCADE")
            conn.commit()
        engine.dispose()
