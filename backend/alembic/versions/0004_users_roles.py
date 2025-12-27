import uuid
from alembic import op
import sqlalchemy as sa


revision = "0004_users_roles"
down_revision = "0003_purchasing_stock"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True)))
    op.execute("UPDATE roles SET name = 'admin' WHERE name = 'manager'")
    roles_table = sa.table("roles", sa.column("id", sa.String()), sa.column("name", sa.String()))
    op.bulk_insert(
        roles_table,
        [
            {"id": str(uuid.uuid4()), "name": "owner"},
            {"id": str(uuid.uuid4()), "name": "admin"},
            {"id": str(uuid.uuid4()), "name": "cashier"},
        ],
    )


def downgrade() -> None:
    op.drop_column("users", "last_login_at")
