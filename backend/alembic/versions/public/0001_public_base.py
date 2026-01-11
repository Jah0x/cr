"""Public schema baseline.

Revision ID: 0001_public_base
Revises:
Create Date: 2025-09-27 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID

revision = "0001_public_base"
down_revision = None
branch_labels = ("public",)
depends_on = None


tenant_status_enum = ENUM("active", "inactive", name="tenantstatus", schema="public", create_type=False)


def upgrade() -> None:
    tenant_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("status", tenant_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema="public",
    )
    op.create_index("ix_tenants_status", "tenants", ["status"], schema="public")
    op.create_index("ix_tenants_code", "tenants", ["code"], unique=True, schema="public")


def downgrade() -> None:
    op.drop_index("ix_tenants_code", table_name="tenants", schema="public")
    op.drop_index("ix_tenants_status", table_name="tenants", schema="public")
    op.drop_table("tenants", schema="public")
    tenant_status_enum.drop(op.get_bind(), checkfirst=True)
