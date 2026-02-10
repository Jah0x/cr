from __future__ import annotations

import asyncio
import logging
import os
import time
import zlib
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from fastapi import HTTPException, status

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.config import get_settings
from app.core.db_utils import quote_ident
from app.core.tenancy import normalize_tenant_slug
from app.models.tenant import TenantStatus
from app.core.db_urls import normalize_migration_database_url

logger = logging.getLogger(__name__)

DEFAULT_VERSION_TABLE = "alembic_version"
LEGACY_PUBLIC_VERSION_TABLE = "alembic_version_public"
LEGACY_TENANT_VERSION_TABLE = "alembic_version_tenant"


class TenantMigrationLockTimeoutError(RuntimeError):
    pass


def _alembic_config(
    *,
    version_locations: list[Path],
    schema: str | None,
    version_table: str | None,
    version_table_schema: str | None,
) -> Config:
    settings = get_settings()
    alembic_ini_path = Path(settings.ALEMBIC_INI_PATH)
    script_location = alembic_ini_path.parent / "alembic"
    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(script_location))
    sync_url = normalize_migration_database_url(settings.database_url)
    config.set_main_option("sqlalchemy.url", sync_url)
    config.set_main_option(
        "version_locations",
        " ".join(str(path) for path in version_locations),
    )
    if version_table:
        config.set_main_option("version_table", version_table)
    if schema:
        config.set_main_option("schema", schema)
    if version_table_schema:
        config.set_main_option("version_table_schema", version_table_schema)
    return config


def _mask_database_url(database_url: str) -> str:
    split = urlsplit(database_url)
    if not split.netloc or "@" not in split.netloc:
        return database_url
    userinfo, hostinfo = split.netloc.rsplit("@", 1)
    username = userinfo.split(":", 1)[0]
    masked_netloc = f"{username}:***@{hostinfo}"
    return urlunsplit((split.scheme, masked_netloc, split.path, split.query, split.fragment))


def _log_migration_start(
    *,
    schema: str,
    branch: str,
    revision_target: str,
    version_table_schema: str | None,
    version_table: str,
    database_url: str,
    correlation_id: str | None,
) -> None:
    logger.info(
        "migration_started schema=%s branch=%s revision=%s version_table_schema=%s version_table=%s url=%s correlation_id=%s",
        schema,
        branch,
        revision_target,
        version_table_schema,
        version_table,
        _mask_database_url(database_url),
        correlation_id,
    )


def _log_schema_table_count(connection, schema: str, stage: str) -> None:
    table_count = connection.execute(
        text(
            """
            select count(*)
            from information_schema.tables
            where table_schema = :schema
            """
        ),
        {"schema": schema},
    ).scalar()
    logger.info("%s table count: schema=%s tables=%s", stage, schema, table_count)


def _advisory_lock_key(schema: str) -> int:
    return int(zlib.crc32(schema.encode("utf-8")))


def _acquire_advisory_lock(
    connection,
    key: int,
    *,
    timeout: int,
    wait: bool,
    schema: str,
    correlation_id: str | None,
) -> None:
    logger.info(
        "lock_acquire_attempt schema=%s lock_key=%s wait_enabled=%s timeout=%s correlation_id=%s",
        schema,
        key,
        wait,
        timeout,
        correlation_id,
    )
    start = time.monotonic()
    got = bool(connection.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": key}).scalar())
    if wait:
        while not got and (time.monotonic() - start) < timeout:
            time.sleep(1)
            got = bool(connection.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": key}).scalar())
    if not got:
        waited = int(time.monotonic() - start)
        logger.warning(
            "lock_acquire_timeout schema=%s lock_key=%s waited=%s correlation_id=%s",
            schema,
            key,
            waited,
            correlation_id,
        )
        raise TenantMigrationLockTimeoutError(
            f"Could not acquire advisory lock for tenant schema={schema} key={key} after {waited}s"
        )
    logger.info("lock_acquired schema=%s lock_key=%s correlation_id=%s", schema, key, correlation_id)


def _release_advisory_lock(connection, key: int, *, schema: str, correlation_id: str | None) -> None:
    try:
        connection.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": key})
        logger.info("lock_released schema=%s lock_key=%s correlation_id=%s", schema, key, correlation_id)
    except Exception:
        logger.exception("Failed to release advisory lock schema=%s key=%s correlation_id=%s", schema, key, correlation_id)


def _table_exists(connection, schema: str, table_name: str) -> bool:
    return bool(
        connection.execute(
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
            {"schema": schema, "table_name": table_name},
        ).scalar()
    )


def _resolve_version_table(connection, schema: str) -> str | None:
    if _table_exists(connection, schema, DEFAULT_VERSION_TABLE):
        return DEFAULT_VERSION_TABLE
    if _table_exists(connection, schema, LEGACY_TENANT_VERSION_TABLE):
        return LEGACY_TENANT_VERSION_TABLE
    if _table_exists(connection, schema, LEGACY_PUBLIC_VERSION_TABLE):
        return LEGACY_PUBLIC_VERSION_TABLE
    return None


def _tenant_script_directory() -> ScriptDirectory:
    settings = get_settings()
    root = Path(settings.ALEMBIC_INI_PATH).parent
    script_location = root / "alembic"
    tenant_versions = script_location / "versions" / "tenant"
    config = _alembic_config(
        version_locations=[tenant_versions],
        schema=None,
        version_table=DEFAULT_VERSION_TABLE,
        version_table_schema=None,
    )
    return ScriptDirectory.from_config(config)


def get_tenant_head_revision() -> str | None:
    script = _tenant_script_directory()
    revisions = script.get_revisions("tenant@head")
    if not revisions:
        return None
    return revisions[0].revision


def get_tenant_migration_status(schema: str) -> dict:
    schema = normalize_tenant_slug(schema)
    engine = create_engine(_sync_database_url())
    head_revision = get_tenant_head_revision()
    with engine.connect() as conn:
        schema_exists = conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.schemata
                    WHERE schema_name = :schema
                )
                """
            ),
            {"schema": schema},
        ).scalar()
        revision = None
        version_table = None
        if schema_exists:
            version_table = _resolve_version_table(conn, schema)
            if version_table:
                safe_schema = quote_ident(schema)
                revision = conn.execute(
                    text(f"SELECT version_num FROM {safe_schema}.{version_table} LIMIT 1")
                ).scalar()
    engine.dispose()
    return {
        "schema": schema,
        "schema_exists": bool(schema_exists),
        "revision": revision,
        "head_revision": head_revision,
        "version_table": version_table,
    }


async def ensure_tenant_ready(session, tenant, *, correlation_id: str | None = None) -> None:
    schema = normalize_tenant_slug(tenant.code)
    status_info = get_tenant_migration_status(schema)
    if not status_info["schema_exists"]:
        detail = f"Tenant schema '{schema}' is missing"
        logger.error(
            "Tenant schema missing: schema=%s correlation_id=%s detail=%s",
            schema,
            correlation_id,
            detail,
        )
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
    head_revision = status_info["head_revision"]
    current_revision = status_info["revision"]
    if head_revision and current_revision != head_revision:
        logger.info(
            "Tenant schema %s not at head (current=%s head=%s version_table=%s) correlation_id=%s",
            schema,
            current_revision,
            head_revision,
            status_info["version_table"],
            correlation_id,
        )
        auto_migrate = os.getenv("ENABLE_AUTO_MIGRATIONS", "").lower() in {"1", "true", "yes", "on"}
        if not auto_migrate:
            detail = (
                f"Tenant schema '{schema}' is not migrated. "
                "Run tenant migrations with the migration CLI or enable auto migrations."
            )
            logger.error(
                "Tenant schema not migrated: schema=%s correlation_id=%s detail=%s",
                schema,
                correlation_id,
                detail,
            )
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
        try:
            await asyncio.to_thread(run_tenant_migrations, schema, correlation_id=correlation_id)
            tenant.status = TenantStatus.active
            tenant.last_error = None
            await session.flush()
        except Exception as exc:
            tenant.status = TenantStatus.provisioning_failed
            tenant.last_error = str(exc)
            await session.flush()
            logger.exception(
                "Tenant migrations failed for schema=%s correlation_id=%s",
                schema,
                correlation_id,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Tenant migrations failed: {exc}",
            ) from exc


def run_public_migrations() -> None:
    settings = get_settings()
    root = Path(settings.ALEMBIC_INI_PATH).parent
    public_versions = root / "alembic" / "versions" / "public"
    config = _alembic_config(
        version_locations=[public_versions],
        schema="public",
        version_table=DEFAULT_VERSION_TABLE,
        version_table_schema="public",
    )
    database_url = _sync_database_url()
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            _ensure_public_version_table(connection)
            config.attributes["connection"] = connection
            _log_migration_start(
                schema="public",
                branch="public",
                revision_target="public@head",
                version_table_schema="public",
                version_table=DEFAULT_VERSION_TABLE,
                database_url=database_url,
                correlation_id=None,
            )
            command.upgrade(config, "public@head")
            connection.commit()
            _log_schema_table_count(connection, "public", "After public migrations")
    finally:
        engine.dispose()


async def verify_public_migrations(engine) -> None:
    async with engine.connect() as conn:
        res = await conn.execute(
            text(
                """
                select
                    to_regclass('public.alembic_version') as alembic,
                    to_regclass('public.modules') as modules,
                    exists(
                        select 1
                        from information_schema.tables
                        where table_schema = 'public'
                          and table_name = 'alembic_version'
                    ) as alembic_exists,
                    exists(
                        select 1
                        from information_schema.tables
                        where table_schema = 'public'
                          and table_name = 'modules'
                    ) as modules_exists
                """
            )
        )
        row = res.mappings().first()

    alembic_ok = row and (row["alembic"] or row["alembic_exists"])
    modules_ok = row and (row["modules"] or row["modules_exists"])
    if not alembic_ok or not modules_ok:
        raise RuntimeError(f"Alembic migration failed: tables not created: {row}")


def run_tenant_migrations(
    schema: str,
    *,
    correlation_id: str | None = None,
    schema_created: bool | None = None,
) -> None:
    schema = normalize_tenant_slug(schema)
    settings = get_settings()
    root = Path(settings.ALEMBIC_INI_PATH).parent
    tenant_versions = root / "alembic" / "versions" / "tenant"
    config = _alembic_config(
        version_locations=[tenant_versions],
        schema=schema,
        version_table=DEFAULT_VERSION_TABLE,
        version_table_schema=schema,
    )
    database_url = _sync_database_url()
    engine = create_engine(database_url)
    lock_key = _advisory_lock_key(schema)
    lock_acquired = False
    migration_start = time.monotonic()
    try:
        with engine.connect() as connection:
            try:
                _acquire_advisory_lock(
                    connection,
                    lock_key,
                    timeout=settings.tenant_migration_lock_timeout,
                    wait=settings.enable_wait_for_migration_lock,
                    schema=schema,
                    correlation_id=correlation_id,
                )
                lock_acquired = True
                allow_stamp = bool(schema_created) or settings.force_stamp_if_tables_exist
                _ensure_tenant_version_table(
                    connection,
                    schema,
                    config,
                    allow_stamp=allow_stamp,
                    correlation_id=correlation_id,
                )
                config.attributes["connection"] = connection
                version_table = _resolve_version_table(connection, schema) or DEFAULT_VERSION_TABLE
                current_revision = None
                if _table_exists(connection, schema, version_table):
                    safe_schema = quote_ident(schema)
                    current_revision = connection.execute(
                        text(f"SELECT version_num FROM {safe_schema}.{version_table} LIMIT 1")
                    ).scalar()
                head_revision = get_tenant_head_revision()
                _log_migration_start(
                    schema=schema,
                    branch="tenant",
                    revision_target="tenant@head",
                    version_table_schema=schema,
                    version_table=DEFAULT_VERSION_TABLE,
                    database_url=database_url,
                    correlation_id=correlation_id,
                )
                logger.info(
                    "migration_status schema=%s current_revision=%s head_revision=%s version_table=%s correlation_id=%s",
                    schema,
                    current_revision,
                    head_revision,
                    version_table,
                    correlation_id,
                )
                command.upgrade(config, "tenant@head")
                connection.commit()
                duration = time.monotonic() - migration_start
                logger.info(
                    "migration_succeeded schema=%s duration_s=%.2f correlation_id=%s",
                    schema,
                    duration,
                    correlation_id,
                )
                _log_schema_table_count(connection, schema, "After tenant migrations")
                _verify_tenant_tables(connection, schema, database_url)
            except Exception:
                duration = time.monotonic() - migration_start
                logger.exception(
                    "migration_failed schema=%s duration_s=%.2f correlation_id=%s",
                    schema,
                    duration,
                    correlation_id,
                )
                raise
            finally:
                if lock_acquired:
                    _release_advisory_lock(connection, lock_key, schema=schema, correlation_id=correlation_id)
    finally:
        engine.dispose()


def _sync_database_url() -> str:
    settings = get_settings()
    return normalize_migration_database_url(settings.database_url)


def _ensure_public_version_table(connection) -> None:
    if _table_exists(connection, "public", DEFAULT_VERSION_TABLE):
        return
    if _table_exists(connection, "public", LEGACY_PUBLIC_VERSION_TABLE):
        connection.exec_driver_sql(
            f"ALTER TABLE public.{LEGACY_PUBLIC_VERSION_TABLE} RENAME TO {DEFAULT_VERSION_TABLE}"
        )
        connection.commit()


def _ensure_tenant_version_table(
    connection,
    schema: str,
    config: Config,
    *,
    allow_stamp: bool,
    correlation_id: str | None,
) -> None:
    if _table_exists(connection, schema, DEFAULT_VERSION_TABLE):
        return
    if _table_exists(connection, schema, LEGACY_TENANT_VERSION_TABLE):
        quoted_schema = quote_ident(schema)
        connection.exec_driver_sql(
            f"ALTER TABLE {quoted_schema}.{LEGACY_TENANT_VERSION_TABLE} RENAME TO {DEFAULT_VERSION_TABLE}"
        )
        connection.commit()
        return
    has_tables = connection.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = :schema
            )
            """
        ),
        {"schema": schema},
    ).scalar()
    if not has_tables:
        return
    if allow_stamp:
        logger.info(
            "Stamping tenant schema at head because version table is missing: schema=%s correlation_id=%s",
            schema,
            correlation_id,
        )
        config.attributes["connection"] = connection
        command.stamp(config, "tenant@head")
        connection.commit()
        return
    raise RuntimeError(
        "Tenant schema has tables but no version table; manual recovery required or "
        "set FORCE_STAMP_IF_TABLES_EXIST=1 to stamp explicitly."
    )


def _verify_tenant_tables(connection, schema: str, database_url: str) -> None:
    quoted_schema = quote_ident(schema)
    category_reg = f"{quoted_schema}.categories"
    product_reg = f"{quoted_schema}.products"
    result = connection.execute(
        text(
            """
            SELECT
                to_regclass(:category) as categories,
                to_regclass(:product) as products
            """
        ),
        {"category": category_reg, "product": product_reg},
    ).mappings().one()
    if not result["categories"] or not result["products"]:
        logger.error(
            "Tenant migration missing tables: schema=%s url=%s categories=%s products=%s",
            schema,
            _mask_database_url(database_url),
            result["categories"],
            result["products"],
        )
        raise RuntimeError(f"Tenant migration did not create required tables in schema '{schema}'.")
