"""Public platform auth tables.

Revision ID: public_0003
Revises: public_0002
Create Date: 2025-09-27 00:00:02.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "public_0003"
down_revision = "public_0002"
branch_labels = ("public",)
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        schema="public",
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True, schema="public")

    op.create_table(
        "roles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        schema="public",
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True, schema="public")

    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("public.users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "role_id",
            UUID(as_uuid=True),
            sa.ForeignKey("public.roles.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        schema="public",
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"], schema="public")
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"], schema="public")


def downgrade() -> None:
    op.drop_index("ix_user_roles_role_id", table_name="user_roles", schema="public")
    op.drop_index("ix_user_roles_user_id", table_name="user_roles", schema="public")
    op.drop_table("user_roles", schema="public")
    op.drop_index("ix_roles_name", table_name="roles", schema="public")
    op.drop_table("roles", schema="public")
    op.drop_index("ix_users_email", table_name="users", schema="public")
    op.drop_table("users", schema="public")
