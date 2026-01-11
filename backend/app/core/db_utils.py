import re

_SCHEMA_RE = re.compile(r"^[a-z0-9_-]+$")


def validate_schema_name(schema: str) -> None:
    if not isinstance(schema, str) or not schema:
        raise ValueError("Schema name must be a non-empty string.")
    if len(schema) > 63:
        raise ValueError("Schema name must be at most 63 characters long.")
    if not _SCHEMA_RE.fullmatch(schema):
        raise ValueError("Schema name may only contain lowercase letters, digits, underscores, and hyphens.")


def quote_ident(schema: str) -> str:
    validate_schema_name(schema)
    escaped = schema.replace('"', '""')
    return f'"{escaped}"'
