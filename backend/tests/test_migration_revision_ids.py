from __future__ import annotations

import ast
from pathlib import Path


def _iter_revision_values(module: ast.Module) -> list[tuple[str, object]]:
    values: list[tuple[str, object]] = []
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"revision", "down_revision"}:
                    values.append((target.id, ast.literal_eval(node.value)))
    return values


def _flatten_revision_values(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (tuple, list, set)):
        return [item for item in value if isinstance(item, str)]
    return []


def test_migration_revision_ids_are_short() -> None:
    migrations_root = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    migration_files = sorted(migrations_root.rglob("*.py"))
    assert migration_files, f"No migration files found under {migrations_root}"

    too_long: list[str] = []
    for migration_file in migration_files:
        module = ast.parse(migration_file.read_text(encoding="utf-8"))
        for name, raw_value in _iter_revision_values(module):
            for value in _flatten_revision_values(raw_value):
                if len(value) > 32:
                    too_long.append(f"{migration_file.relative_to(migrations_root)}:{name}={value}")

    assert not too_long, "Found revision identifiers longer than 32 chars:\n" + "\n".join(too_long)
