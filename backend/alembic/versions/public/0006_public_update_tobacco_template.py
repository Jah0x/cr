"""Update tobacco template modules and features.

Revision ID: public_0007
Revises: public_0006
Create Date: 2025-09-27 01:05:00.000000
"""

from alembic import op

revision = "public_0007"
down_revision = "public_0006"
branch_labels = ("public",)
depends_on = None

MODULE_CODES = [
    "catalog",
    "purchasing",
    "stock",
    "sales",
    "pos",
    "users",
    "reports",
    "finance",
]
FEATURE_CODES = [
    "reports",
    "ui_prefs",
    "pos.age_confirm",
]


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO public.modules (id, code, name, description, is_active, created_at)
        VALUES
            ('57f8433a-1e63-4cd6-8ae0-4cb2a430e6e3', 'users', 'Users', NULL, TRUE, now()),
            ('2c6ab839-6d44-4937-8a56-9c86fa6e7f6b', 'finance', 'Finance', NULL, TRUE, now())
        ON CONFLICT (code) DO NOTHING;
        """
    )
    op.execute(
        """
        INSERT INTO public.features (id, code, name, description, is_active, created_at)
        VALUES
            ('9c1a8bf0-96b0-4525-9f4f-9b4be1a3f8ef', 'reports', 'Reports', NULL, TRUE, now()),
            ('e3bc29d2-2348-4e4f-8ba2-29f41aa69b66', 'ui_prefs', 'UI Preferences', NULL, TRUE, now())
        ON CONFLICT (code) DO NOTHING;
        """
    )
    op.execute(
        """
        INSERT INTO public.templates (id, name, description, module_codes, feature_codes, created_at)
        VALUES (
            'd8977528-7003-4e37-a819-4ec63689377a',
            'tobacco',
            NULL,
            '[]'::jsonb,
            '[]'::jsonb,
            now()
        )
        ON CONFLICT (name) DO NOTHING;
        """
    )
    module_codes = ", ".join([f'"{code}"' for code in MODULE_CODES])
    feature_codes = ", ".join([f'"{code}"' for code in FEATURE_CODES])
    op.execute(
        f"""
        UPDATE public.templates
        SET module_codes = '[{module_codes}]'::jsonb,
            feature_codes = '[{feature_codes}]'::jsonb
        WHERE name = 'tobacco';
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE public.templates
        SET module_codes = '[]'::jsonb,
            feature_codes = '[]'::jsonb
        WHERE name = 'tobacco';
        """
    )
    op.execute("DELETE FROM public.features WHERE code IN ('reports', 'ui_prefs');")
    op.execute("DELETE FROM public.modules WHERE code IN ('users', 'finance');")
