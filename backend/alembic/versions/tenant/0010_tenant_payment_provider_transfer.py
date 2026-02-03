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
    op.execute("ALTER TYPE paymentprovider RENAME VALUE 'external' TO 'transfer'")


def downgrade() -> None:
    op.execute("ALTER TYPE paymentprovider RENAME VALUE 'transfer' TO 'external'")
