import os
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.core.db_urls import normalize_migration_database_url


def _build_alembic_config(base_dir: Path, database_url: str) -> Config:
    alembic_ini_path = base_dir / "alembic.ini"
    script_location = base_dir / "alembic"
    public_versions = "alembic/versions/public"
    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(script_location))
    config.set_main_option("sqlalchemy.url", normalize_migration_database_url(database_url))
    config.set_main_option("version_locations", str(public_versions))
    config.set_main_option("version_table", "alembic_version")
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


def _post_migration_check(database_url: str) -> None:
    sync_url = normalize_migration_database_url(database_url)
    engine = create_engine(sync_url)
    try:
        with engine.connect() as conn:
            info_row = conn.execute(
                text("select current_database(), current_user, current_schema()")
            ).one()
            check_row = (
                conn.execute(
                    text(
                        """
                        select
                            to_regclass('public.alembic_version') as alembic_version,
                            to_regclass('public.tenants') as tenants,
                            to_regclass('public.modules') as modules,
                            to_regclass('public.tenant_settings') as tenant_settings
                        """
                    )
                )
            ).mappings().one()
    finally:
        engine.dispose()

    missing = [key for key, value in check_row.items() if value is None]
    if missing:
        masked_url = _mask_database_url(sync_url)
        message = (
            "Post-migration check failed. Database info: "
            f"db={info_row[0]}, user={info_row[1]}, schema={info_row[2]}. "
            f"Missing tables: {', '.join(missing)}. URL={masked_url}"
        )
        raise RuntimeError(message)


def main() -> None:
    database_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_DSN")
    if not database_url:
        sys.stderr.write("DATABASE_URL or DATABASE_DSN is required to run migrations.\n")
        sys.exit(1)

    base_dir = Path("/app")
    config = _build_alembic_config(base_dir, database_url)

    try:
        command.upgrade(config, "head")
        _post_migration_check(database_url)
    except Exception as exc:
        sys.stderr.write(f"Migration failed: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
