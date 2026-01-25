import re

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

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


async def set_search_path(session: AsyncSession, schema: str | None) -> None:
    if schema is None:
        await session.execute(text("SET LOCAL search_path TO public"))
        return
    validate_schema_name(schema)
    await session.execute(text(f'SET LOCAL search_path TO "{schema}", public'))


async def list_tables(session: AsyncSession, schema: str | None = None) -> set[str]:
    async with session.connection() as conn:
        def _load_tables(sync_conn):
            inspector = inspect(sync_conn)
            if schema is not None:
                tables = inspector.get_table_names(schema=schema)
                if schema == "public" and not tables:
                    tables = inspector.get_table_names()
                return tables
            return inspector.get_table_names()

        tables = await conn.run_sync(_load_tables)
    return set(tables)
