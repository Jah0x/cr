from alembic import op
import sqlalchemy as sa
import uuid
from sqlalchemy.dialects import postgresql

revision = "0002_catalog"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), default=True),
    )
    op.create_table(
        "brands",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), default=True),
    )
    op.create_table(
        "product_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
    )
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("sku", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL")),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("brands.id", ondelete="SET NULL")),
        sa.Column("line_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_lines.id", ondelete="SET NULL")),
        sa.Column("price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), default=True),
    )
    op.execute(
        "INSERT INTO roles (id, name) VALUES (:id, :name) ON CONFLICT (name) DO NOTHING",
        {"id": str(uuid.uuid4()), "name": "owner"},
    )
    op.execute(
        "INSERT INTO roles (id, name) VALUES (:id, :name) ON CONFLICT (name) DO NOTHING",
        {"id": str(uuid.uuid4()), "name": "manager"},
    )
    op.execute(
        "INSERT INTO roles (id, name) VALUES (:id, :name) ON CONFLICT (name) DO NOTHING",
        {"id": str(uuid.uuid4()), "name": "cashier"},
    )


def downgrade() -> None:
    op.drop_table("products")
    op.drop_table("product_lines")
    op.drop_table("brands")
    op.drop_table("categories")
