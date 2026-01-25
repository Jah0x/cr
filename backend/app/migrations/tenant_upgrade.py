import argparse
import os
import sys

from app.core.tenancy import normalize_tenant_slug
from app.services.migrations import run_tenant_migrations


def main() -> None:
    parser = argparse.ArgumentParser(description="Run tenant alembic migrations.")
    parser.add_argument("--schema", default=os.getenv("TENANT_SCHEMA", "public"))
    args = parser.parse_args()

    try:
        schema = normalize_tenant_slug(args.schema)
    except ValueError as exc:
        sys.stderr.write(f"Invalid tenant schema: {exc}\n")
        sys.exit(1)

    try:
        run_tenant_migrations(schema)
    except Exception as exc:
        sys.stderr.write(f"Tenant migration failed: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
