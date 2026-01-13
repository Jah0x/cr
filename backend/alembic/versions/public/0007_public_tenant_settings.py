"""Add tenant settings storage.

Revision ID: 0007_public_tenant_settings
Revises: 0006_public_update_tobacco_template
Create Date: 2025-10-02 00:00:00.000000
"""

import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0007"
down_revision = "0006"
branch_labels = ("public",)
depends_on = None


DEFAULT_TOBACCO_SETTINGS = {
    "catalog_hierarchy": {
        "levels": [
            {"code": "manufacturer", "title": "Производитель", "enabled": True},
            {"code": "model", "title": "Модель", "enabled": True},
            {"code": "flavor", "title": "Вкус", "enabled": True},
        ]
    }
}


def upgrade() -> None:
    settings_json = json.dumps(DEFAULT_TOBACCO_SETTINGS)
    op.create_table(
        "tenant_settings",
        sa.Column("tenant_id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("settings", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["public.tenants.id"], ondelete="CASCADE"),
        schema="public",
    )
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO public.tenant_settings (tenant_id, settings, updated_at)
            SELECT id, :settings::jsonb, now()
            FROM public.tenants
            ON CONFLICT (tenant_id) DO NOTHING;
            """
        ).bindparams(settings=settings_json)
    )
    conn.execute(
        sa.text(
            """
            UPDATE public.tenant_settings
            SET settings = :settings::jsonb,
                updated_at = now()
            WHERE settings = '{}'::jsonb;
            """
        ).bindparams(settings=settings_json)
    )


def downgrade() -> None:
    op.drop_table("tenant_settings", schema="public")
