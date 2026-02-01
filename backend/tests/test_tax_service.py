from decimal import Decimal

from app.services.tax_service import calculate_sale_tax_lines


def test_exclusive_tax_applies_by_method() -> None:
    settings = {
        "enabled": True,
        "mode": "exclusive",
        "rounding": "round",
        "rules": [
            {"id": "vat", "name": "VAT", "rate": 20, "is_active": True, "applies_to": ["cash"]}
        ],
    }
    lines = calculate_sale_tax_lines(
        Decimal("1000"),
        [{"amount": Decimal("1000"), "method": "cash"}],
        settings,
    )
    assert sum(line["tax_amount"] for line in lines) == Decimal("200.00")


def test_tax_applies_to_payment_share() -> None:
    settings = {
        "enabled": True,
        "mode": "exclusive",
        "rounding": "round",
        "rules": [
            {"id": "vat", "name": "VAT", "rate": 20, "is_active": True, "applies_to": ["cash"]}
        ],
    }
    lines = calculate_sale_tax_lines(
        Decimal("1000"),
        [
            {"amount": Decimal("500"), "method": "cash"},
            {"amount": Decimal("500"), "method": "card"},
        ],
        settings,
    )
    assert sum(line["tax_amount"] for line in lines) == Decimal("100.00")


def test_inclusive_tax_calculation() -> None:
    settings = {
        "enabled": True,
        "mode": "inclusive",
        "rounding": "round",
        "rules": [
            {"id": "vat", "name": "VAT", "rate": 20, "is_active": True, "applies_to": ["cash"]}
        ],
    }
    lines = calculate_sale_tax_lines(
        Decimal("1200"),
        [{"amount": Decimal("1200"), "method": "cash"}],
        settings,
    )
    assert sum(line["tax_amount"] for line in lines) == Decimal("200.00")
