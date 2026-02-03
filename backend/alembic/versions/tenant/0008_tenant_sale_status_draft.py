"""Update sale status enum with draft and cancelled.

Revision ID: tenant_0008
Revises: tenant_0007
Create Date: 2025-10-13 00:00:01.000000
"""

from alembic import op

revision = "tenant_0008"
down_revision = "tenant_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE salestatus RENAME TO salestatus_old")
    op.execute("CREATE TYPE salestatus AS ENUM ('draft', 'completed', 'cancelled')")
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
    op.execute("DROP TYPE salestatus_old")


def downgrade() -> None:
    op.execute("ALTER TYPE salestatus RENAME TO salestatus_new")
    op.execute("CREATE TYPE salestatus AS ENUM ('completed', 'void')")
    op.execute(
        """
        ALTER TABLE sales
        ALTER COLUMN status TYPE salestatus
        USING (
            CASE
                WHEN status::text = 'cancelled' THEN 'void'
                ELSE status::text
            END
        )::salestatus
        """
    )
    op.execute("ALTER TABLE sales ALTER COLUMN status SET DEFAULT 'completed'")
    op.execute("DROP TYPE salestatus_new")
