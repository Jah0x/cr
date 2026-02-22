from __future__ import annotations

import ast
from pathlib import Path


def _get_revision_value(path: Path) -> str | None:
    module = ast.parse(path.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "revision":
                    value = ast.literal_eval(node.value)
                    if isinstance(value, str):
                        return value
    return None


def test_public_head_revision_file_exists() -> None:
    root = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "public"
    migration_files = sorted(root.glob("*.py"))
    assert migration_files, "Public migrations are missing"

    revisions = []
    for migration_file in migration_files:
        revision = _get_revision_value(migration_file)
        if revision and revision.startswith("public_"):
            revisions.append((migration_file.name, revision))

    assert revisions, "Public revision identifiers are missing"
    head_revision = sorted(revisions, key=lambda item: item[1])[-1][1]
    head_suffix = head_revision.split("_", 1)[1]
    has_matching_file = any(file.name.startswith(f"{head_suffix}_") for file in migration_files)
    assert has_matching_file, f"Missing public migration file prefixed with head revision suffix {head_suffix}"
