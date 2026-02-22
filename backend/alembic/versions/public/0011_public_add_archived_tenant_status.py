"""Add archived status for tenants.

Revision ID: public_0011
Revises: public_0010
Create Date: 2026-02-06 00:00:01.000000
"""

from alembic import op

revision = "public_0011"
down_revision = "public_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE public.tenantstatus ADD VALUE IF NOT EXISTS 'archived'")


def downgrade() -> None:
    # PostgreSQL ENUM values are not safely removable in downgrade.
    pass
