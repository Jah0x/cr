"""Add send_to_terminal flag to sales.

Revision ID: tenant_0009
Revises: tenant_0008
Create Date: 2025-10-13 00:00:02.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "tenant_0009"
down_revision = "tenant_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sales",
        sa.Column("send_to_terminal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("sales", "send_to_terminal")
