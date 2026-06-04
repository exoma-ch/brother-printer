"""ADR-0002: CLI must not import transport or protocol directly."""

from __future__ import annotations

import ast
from pathlib import Path

_CLI_DIR = Path(__file__).resolve().parents[2] / "src" / "brother_ptouch_driver" / "cli"
_FORBIDDEN_PREFIXES = (
    "brother_ptouch_driver.transport",
    "brother_ptouch_driver.protocol",
)


def _forbidden_imports_in(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(_FORBIDDEN_PREFIXES):
                    found.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith(_FORBIDDEN_PREFIXES):
                found.append(node.module)
    return found


def test_cli_does_not_import_transport_or_protocol():
    """CLI modules import only from the brother_ptouch_driver library API surface."""
    violations: list[str] = []
    for path in sorted(_CLI_DIR.glob("*.py")):
        for name in _forbidden_imports_in(path):
            violations.append(f"{path.name}: {name}")
    assert violations == []
