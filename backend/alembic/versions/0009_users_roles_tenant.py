import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0009_users_roles_tenant"
down_revision = "0008_tenants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    tenant_id = str(uuid.uuid4())
    existing = conn.execute(sa.text("SELECT id FROM tenants WHERE code = :code"), {"code": "default"}).scalar()
    if existing:
        tenant_id = str(existing)
    else:
        conn.execute(
            sa.text(
                "INSERT INTO tenants (id, name, code, status, created_at, updated_at) "
                "VALUES (:id, :name, :code, 'active', timezone('utc', now()), timezone('utc', now()))"
            ),
            {"id": tenant_id, "name": "Default", "code": "default"},
        )

    op.add_column("users", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("roles", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("user_roles", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.execute(sa.text("UPDATE users SET tenant_id = :tenant_id WHERE tenant_id IS NULL"), {"tenant_id": tenant_id})
    op.execute(sa.text("UPDATE roles SET tenant_id = :tenant_id WHERE tenant_id IS NULL"), {"tenant_id": tenant_id})
    op.execute(sa.text("UPDATE user_roles SET tenant_id = :tenant_id WHERE tenant_id IS NULL"), {"tenant_id": tenant_id})

    op.alter_column("users", "tenant_id", nullable=False)
    op.alter_column("roles", "tenant_id", nullable=False)
    op.alter_column("user_roles", "tenant_id", nullable=False)

    op.create_foreign_key("fk_users_tenant_id", "users", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_roles_tenant_id", "roles", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("fk_user_roles_tenant_id", "user_roles", "tenants", ["tenant_id"], ["id"], ondelete="RESTRICT")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_roles_name", table_name="roles")

    op.create_index("ix_users_tenant_id", "users", ["tenant_id"], unique=False)
    op.create_index("ix_users_email_tenant", "users", ["email", "tenant_id"], unique=True)
    op.create_index("ix_roles_tenant_id", "roles", ["tenant_id"], unique=False)
    op.create_index("ix_roles_name_tenant", "roles", ["name", "tenant_id"], unique=True)
    op.create_index("ix_user_roles_tenant_id", "user_roles", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_roles_tenant_id", table_name="user_roles")
    op.drop_index("ix_roles_name_tenant", table_name="roles")
    op.drop_index("ix_roles_tenant_id", table_name="roles")
    op.drop_index("ix_users_email_tenant", table_name="users")
    op.drop_index("ix_users_tenant_id", table_name="users")

    op.drop_constraint("fk_user_roles_tenant_id", "user_roles", type_="foreignkey")
    op.drop_constraint("fk_roles_tenant_id", "roles", type_="foreignkey")
    op.drop_constraint("fk_users_tenant_id", "users", type_="foreignkey")

    op.drop_column("user_roles", "tenant_id")
    op.drop_column("roles", "tenant_id")
    op.drop_column("users", "tenant_id")

    op.create_index("ix_roles_name", "roles", ["name"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
