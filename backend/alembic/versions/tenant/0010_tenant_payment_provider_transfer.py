"""Rename payment provider external to transfer.

Revision ID: tenant_0010
Revises: tenant_0009
Create Date: 2025-10-14 00:00:00.000000
"""

from alembic import op

revision = "tenant_0010"
down_revision = "tenant_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'paymentprovider' AND e.enumlabel = 'external'
            ) AND NOT EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'paymentprovider' AND e.enumlabel = 'transfer'
            ) THEN
                ALTER TYPE paymentprovider RENAME VALUE 'external' TO 'transfer';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'paymentprovider' AND e.enumlabel = 'transfer'
            ) AND NOT EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON t.oid = e.enumtypid
                WHERE t.typname = 'paymentprovider' AND e.enumlabel = 'external'
            ) THEN
                ALTER TYPE paymentprovider RENAME VALUE 'transfer' TO 'external';
            END IF;
        END
        $$;
        """
    )
