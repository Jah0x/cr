from __future__ import annotations

import ast
import sys
from collections import Counter
from pathlib import Path


def _extract_branch_labels(module: ast.Module) -> list[str]:
    labels: list[str] = []
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id != "branch_labels":
                continue
            value = ast.literal_eval(node.value)
            if value is None:
                return []
            if isinstance(value, (list, tuple)):
                return [str(item) for item in value]
            return [str(value)]
    return labels


def main() -> int:
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    counts: Counter[str] = Counter()
    duplicates: dict[str, list[str]] = {}

    for path in sorted(versions_dir.rglob("*.py")):
        module = ast.parse(path.read_text())
        labels = _extract_branch_labels(module)
        for label in labels:
            counts[label] += 1
            if counts[label] > 1:
                duplicates.setdefault(label, []).append(str(path))

    if duplicates:
        for label, paths in duplicates.items():
            unique_paths = ", ".join(sorted(set(paths)))
            print(f"branch_labels '{label}' appears more than once in: {unique_paths}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
