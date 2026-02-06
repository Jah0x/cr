"""Update sale status enum with draft and cancelled.

Revision ID: tenant_0008
Revises: tenant_0007
Create Date: 2025-10-13 00:00:01.000000
"""

from alembic import op
from sqlalchemy import text

revision = "tenant_0008"
down_revision = "tenant_0007"
branch_labels = None
depends_on = None


OLD_ENUM_VALUES = ("completed", "void")
NEW_ENUM_VALUES = ("draft", "completed", "cancelled")



def _type_exists(type_name: str) -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            text(
                """
                SELECT 1
                FROM pg_type t
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE t.typname = :type_name
                  AND n.nspname = current_schema()
                LIMIT 1
                """
            ),
            {"type_name": type_name},
        ).scalar()
    )



def _create_enum_type_if_missing(type_name: str, values: tuple[str, ...]) -> None:
    if _type_exists(type_name):
        return

    values_sql = ", ".join(f"'{value}'" for value in values)
    op.execute(f"CREATE TYPE {type_name} AS ENUM ({values_sql})")



def _drop_type_if_exists(type_name: str) -> None:
    if _type_exists(type_name):
        op.execute(f"DROP TYPE {type_name}")



def _get_sales_status_udt_name() -> str | None:
    bind = op.get_bind()
    return bind.execute(
        text(
            """
            SELECT c.udt_name
            FROM information_schema.columns c
            WHERE c.table_schema = current_schema()
              AND c.table_name = 'sales'
              AND c.column_name = 'status'
            LIMIT 1
            """
        )
    ).scalar()



def upgrade() -> None:
    current_status_type = _get_sales_status_udt_name()

    if current_status_type == "salestatus_old" and not _type_exists("salestatus"):
        _create_enum_type_if_missing("salestatus", NEW_ENUM_VALUES)

    if _type_exists("salestatus") and _type_exists("salestatus_old"):
        # Non-standard state after partially applied migration: keep the expected target type.
        _drop_type_if_exists("salestatus_old")

    if current_status_type == "salestatus":
        if _type_exists("salestatus_old"):
            _drop_type_if_exists("salestatus_old")
        return

    if current_status_type == "salestatus_old":
        _create_enum_type_if_missing("salestatus", NEW_ENUM_VALUES)
        op.execute(
            """
            ALTER TABLE sales
            ALTER COLUMN status TYPE salestatus
            USING (
                CASE
                    WHEN status::text = 'void' THEN 'cancelled'
                    ELSE status::text
                END
            )::salestatus
            """
        )
        op.execute("ALTER TABLE sales ALTER COLUMN status SET DEFAULT 'draft'")
        _drop_type_if_exists("salestatus_old")
        return

    if _type_exists("salestatus"):
        # Type exists but column is not aligned (e.g. reset column type in an ad-hoc way).
        op.execute(
            """
            ALTER TABLE sales
            ALTER COLUMN status TYPE salestatus
            USING (
                CASE
                    WHEN status::text = 'void' THEN 'cancelled'
                    ELSE status::text
                END
            )::salestatus
            """
        )
        op.execute("ALTER TABLE sales ALTER COLUMN status SET DEFAULT 'draft'")
        _drop_type_if_exists("salestatus_old")
        return

    if current_status_type is None and not _type_exists("salestatus"):
        _create_enum_type_if_missing("salestatus", NEW_ENUM_VALUES)



def downgrade() -> None:
    current_status_type = _get_sales_status_udt_name()

    _create_enum_type_if_missing("salestatus_old", OLD_ENUM_VALUES)

    if current_status_type != "salestatus_old":
        op.execute(
            """
            ALTER TABLE sales
            ALTER COLUMN status TYPE salestatus_old
            USING (
                CASE
                    WHEN status::text = 'cancelled' THEN 'void'
                    WHEN status::text = 'draft' THEN 'completed'
                    ELSE status::text
                END
            )::salestatus_old
            """
        )
    op.execute("ALTER TABLE sales ALTER COLUMN status SET DEFAULT 'completed'")

    if _type_exists("salestatus"):
        _drop_type_if_exists("salestatus")

    if not _type_exists("salestatus") and _type_exists("salestatus_old"):
        op.execute("ALTER TYPE salestatus_old RENAME TO salestatus")
