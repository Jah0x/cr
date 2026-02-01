from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING, ROUND_FLOOR

from app.models.sales import PaymentProvider


PAYMENT_METHODS = [method.value for method in PaymentProvider]


def _round_amount(value: Decimal, rounding: str) -> Decimal:
    quantize = Decimal("0.01")
    if rounding == "ceil":
        return value.quantize(quantize, rounding=ROUND_CEILING)
    if rounding == "floor":
        return value.quantize(quantize, rounding=ROUND_FLOOR)
    return value.quantize(quantize, rounding=ROUND_HALF_UP)


def _normalize_applies_to(raw_value: object) -> list[str]:
    if isinstance(raw_value, list):
        filtered = [value for value in raw_value if value in PAYMENT_METHODS]
        if filtered:
            return filtered
    return PAYMENT_METHODS.copy()


def calculate_sale_tax_lines(
    subtotal: Decimal,
    payments: list[dict] | None,
    tax_settings: dict | None,
) -> list[dict]:
    if not tax_settings or not tax_settings.get("enabled"):
        return []

    rules = []
    for rule in tax_settings.get("rules", []) or []:
        if not rule.get("is_active"):
            continue
        rate = Decimal(str(rule.get("rate", 0) or 0))
        if rate <= 0:
            continue
        rules.append(
            {
                "id": str(rule.get("id")),
                "name": str(rule.get("name", "")),
                "rate": rate,
                "applies_to": _normalize_applies_to(rule.get("applies_to")),
            }
        )

    if not rules:
        return []

    rounding = tax_settings.get("rounding", "round")
    mode = tax_settings.get("mode", "exclusive")

    payments = payments or []
    method_totals: dict[str, Decimal] = {method: Decimal("0") for method in PAYMENT_METHODS}
    for payment in payments:
        method = payment.get("method")
        if isinstance(method, PaymentProvider):
            method = method.value
        if method not in method_totals:
            continue
        amount = Decimal(str(payment.get("amount", 0) or 0))
        if amount <= 0:
            continue
        method_totals[method] += amount

    total_paid = sum(method_totals.values())
    method_shares: list[tuple[str | None, Decimal]] = []
    if total_paid > 0:
        for method, amount in method_totals.items():
            if amount <= 0:
                continue
            method_shares.append((method, amount / total_paid))
    else:
        method_shares.append((None, Decimal("1")))

    lines: list[dict] = []
    for method, share in method_shares:
        gross_method = subtotal * share
        if gross_method <= 0:
            continue
        if method is None:
            applicable_rules = rules
        else:
            applicable_rules = [rule for rule in rules if method in rule["applies_to"]]
        if not applicable_rules:
            continue

        if mode == "inclusive":
            total_rate = sum(rule["rate"] for rule in applicable_rules)
            if total_rate <= 0:
                continue
            divisor = Decimal("1") + (total_rate / Decimal("100"))
            if divisor <= 0:
                continue
            tax_total = gross_method - (gross_method / divisor)
            for rule in applicable_rules:
                tax_amount = tax_total * (rule["rate"] / total_rate)
                rounded_tax = _round_amount(tax_amount, rounding)
                if rounded_tax <= 0:
                    continue
                lines.append(
                    {
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "rate": rule["rate"],
                        "method": method,
                        "taxable_amount": _round_amount(gross_method, rounding),
                        "tax_amount": rounded_tax,
                    }
                )
        else:
            for rule in applicable_rules:
                tax_amount = gross_method * (rule["rate"] / Decimal("100"))
                rounded_tax = _round_amount(tax_amount, rounding)
                if rounded_tax <= 0:
                    continue
                lines.append(
                    {
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "rate": rule["rate"],
                        "method": method,
                        "taxable_amount": _round_amount(gross_method, rounding),
                        "tax_amount": rounded_tax,
                    }
                )

    return lines
