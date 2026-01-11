"""Seed modules, feature, and tobacco template.

Revision ID: 0005_public_seed_tobacco_template
Revises: 0004_public_features
Create Date: 2025-09-27 00:30:00.000000
"""

from alembic import op

revision = "0005_public_seed_tobacco_template"
down_revision = "0004_public_features"
branch_labels = ("public",)
depends_on = None

MODULE_CODES = (
    "catalog",
    "purchasing",
    "stock",
    "sales",
    "pos",
    "reports",
)


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO public.modules (id, code, name, description, is_active, created_at)
        VALUES
            ('bf8cbe9a-ff56-475f-936c-b33e69d1ff52', 'catalog', 'Catalog', NULL, TRUE, now()),
            ('c529bc87-f948-482c-87ec-1d923d779857', 'purchasing', 'Purchasing', NULL, TRUE, now()),
            ('6afccbd1-0243-402f-a1a7-368576c548d6', 'stock', 'Stock', NULL, TRUE, now()),
            ('c1eee79b-4424-4957-b972-d3c346ab3c36', 'sales', 'Sales', NULL, TRUE, now()),
            ('165f55cc-ee56-4ece-898a-ed6653029c65', 'pos', 'POS', NULL, TRUE, now()),
            ('5808ed91-58c6-4bec-9d9f-436d822f9da8', 'reports', 'Reports', NULL, TRUE, now())
        ON CONFLICT (code) DO NOTHING;
        """
    )
    op.execute(
        """
        INSERT INTO public.features (id, code, name, description, is_active, created_at)
        VALUES
            ('51a6dd06-2f50-48d9-af40-cb642ead6053', 'pos.age_confirm', 'POS Age Confirmation', NULL, TRUE, now())
        ON CONFLICT (code) DO NOTHING;
        """
    )
    op.execute(
        """
        INSERT INTO public.templates (id, name, description, module_codes, feature_codes, created_at)
        VALUES
            (
                'd8977528-7003-4e37-a819-4ec63689377a',
                'tobacco',
                NULL,
                '["catalog", "purchasing", "stock", "sales", "pos", "reports"]'::jsonb,
                '["pos.age_confirm"]'::jsonb,
                now()
            )
        ON CONFLICT (name) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM public.templates WHERE name = 'tobacco';")
    op.execute("DELETE FROM public.features WHERE code = 'pos.age_confirm';")
    op.execute(
        """
        DELETE FROM public.modules
        WHERE code IN ('catalog', 'purchasing', 'stock', 'sales', 'pos', 'reports');
        """
    )
