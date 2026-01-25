import logging
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, create_engine, text

from app.core.db_urls import normalize_migration_database_url

logger = logging.getLogger(__name__)


def _build_alembic_config(base_dir: Path, database_url: str) -> Config:
    alembic_ini_path = base_dir / "alembic.ini"
    script_location = base_dir / "alembic"
    public_versions = script_location / "versions" / "public"
    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(script_location))
    config.set_main_option("sqlalchemy.url", normalize_migration_database_url(database_url))
    config.set_main_option("version_locations", f"{public_versions}")
    config.set_main_option("schema", "public")
    config.set_main_option("version_table_schema", "public")
    return config


def _mask_database_url(database_url: str) -> str:
    split = urlsplit(database_url)
    if not split.netloc or "@" not in split.netloc:
        return database_url
    userinfo, hostinfo = split.netloc.rsplit("@", 1)
    username = userinfo.split(":", 1)[0]
    masked_netloc = f"{username}:***@{hostinfo}"
    return urlunsplit((split.scheme, masked_netloc, split.path, split.query, split.fragment))


def _log_connection_diagnostics(connection: Connection, stage: str) -> None:
    info_row = connection.execute(
        text(
            "select current_database(), current_user, current_schema(), inet_server_addr(), inet_server_port()"
        )
    ).one()
    search_path = connection.execute(text("show search_path")).scalar()
    logger.info(
        "%s: db=%s user=%s schema=%s addr=%s port=%s",
        stage,
        info_row[0],
        info_row[1],
        info_row[2],
        info_row[3],
        info_row[4],
    )
    logger.info("%s: search_path=%s", stage, search_path)


def _post_migration_check(connection: Connection, database_url: str) -> None:
    check_row = (
        connection.execute(
            text(
                """
                select
                    to_regclass('public.alembic_version') as alembic_version,
                    to_regclass('public.tenants') as tenants,
                    to_regclass('public.modules') as modules,
                    to_regclass('public.tenant_settings') as tenant_settings,
                    to_regclass('public.users') as users,
                    to_regclass('public.roles') as roles,
                    to_regclass('public.user_roles') as user_roles
                """
            )
        )
    ).mappings().one()
    logger.info("Post-migration table presence: %s", dict(check_row))
    tables = connection.execute(
        text(
            """
            select table_name
            from information_schema.tables
            where table_schema='public'
            order by table_name
            limit 30
            """
        )
    ).scalars()
    logger.info("Public tables (first 30): %s", list(tables))

    missing = [key for key, value in check_row.items() if value is None]
    if missing:
        masked_url = _mask_database_url(normalize_migration_database_url(database_url))
        raise RuntimeError(
            "Post-migration check failed. Missing tables: "
            f"{', '.join(missing)}. URL={masked_url}"
        )


def run_public_migrations(config: Config) -> None:
    script = ScriptDirectory.from_config(config)
    script_location = config.get_main_option("script_location")
    version_locations = config.get_main_option("version_locations")
    logger.info("Alembic script_location=%s", script_location)
    logger.info("Alembic version_locations=%s", version_locations)
    public_revisions = script.get_revisions("public@head")
    logger.info(
        "Public revisions: %s",
        [revision.revision for revision in public_revisions],
    )
    if not public_revisions:
        raise RuntimeError("No alembic revisions found for public schema")

    logger.info("Running public alembic upgrade to head")
    command.upgrade(config, "public@head")
    logger.info("Public migrations completed")


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    database_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_DSN")
    if not database_url:
        sys.stderr.write("DATABASE_URL or DATABASE_DSN is required to run migrations.\n")
        sys.exit(1)

    base_dir = Path(__file__).resolve().parents[2]
    alembic_ini_path = base_dir / "alembic.ini"
    versions_path = base_dir / "alembic" / "versions"
    if not alembic_ini_path.is_file():
        raise FileNotFoundError(f"alembic.ini not found at {alembic_ini_path}")
    if not versions_path.is_dir():
        raise FileNotFoundError(f"alembic versions directory not found at {versions_path}")
    config = _build_alembic_config(base_dir, database_url)

    sync_url = normalize_migration_database_url(database_url)
    engine = create_engine(sync_url)
    try:
        try:
            with engine.connect() as connection:
                _log_connection_diagnostics(connection, "Before migrations")
                config.attributes["connection"] = connection
                run_public_migrations(config)
                connection.commit()
                _log_connection_diagnostics(connection, "After migrations")
        except Exception as exc:
            sys.stderr.write(f"Migration failed: {exc}\n")
            sys.exit(1)

        engine.dispose()
        engine = create_engine(sync_url)

        try:
            with engine.connect() as connection:
                _post_migration_check(connection, database_url)
        except Exception as exc:
            sys.stderr.write(f"Post-migration check failed: {exc}\n")
            sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
