import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_tenants"
down_revision = "0007_sales_cash_registers"
branch_labels = None
depends_on = None


tenant_status = sa.Enum("active", "inactive", name="tenantstatus")
tenant_status_column = sa.Enum("active", "inactive", name="tenantstatus", create_type=False)


def upgrade() -> None:
    tenant_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("status", tenant_status_column, nullable=False, server_default="active"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        if_not_exists=True,
    )
    op.create_index("ix_tenants_status", "tenants", ["status"], if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_tenants_status", table_name="tenants", if_exists=True)
    op.drop_table("tenants", if_exists=True)
    tenant_status.drop(op.get_bind(), checkfirst=True)
