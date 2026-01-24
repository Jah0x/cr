import re


TENANT_SLUG_RE = re.compile(r"^[a-z0-9_-]{1,63}$")
CODE_RE = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,61}[a-z0-9])?$")
NAME_SLUG_RE = re.compile(r"[^a-z0-9]+")


def normalize_tenant_slug(value: str) -> str:
    slug = value.strip().lower()
    if not slug or not TENANT_SLUG_RE.match(slug):
        raise ValueError("Invalid tenant slug")
    return slug


def slugify_tenant_name(value: str) -> str:
    slug = value.strip().lower()
    slug = NAME_SLUG_RE.sub("-", slug).strip("-")
    if not slug:
        raise ValueError("Invalid tenant name")
    return normalize_tenant_slug(slug)


def normalize_code(value: str) -> str:
    code = value.strip().lower()
    if not code or not CODE_RE.match(code):
        raise ValueError("Invalid code")
    return code


def is_valid_tenant_slug(value: str) -> bool:
    try:
        normalize_tenant_slug(value)
    except ValueError:
        return False
    return True


def build_search_path(schema: str | None) -> str:
    if not schema:
        return "SET LOCAL search_path TO public"
    safe_schema = normalize_tenant_slug(schema)
    return f'SET LOCAL search_path TO "{safe_schema}", public'
