"""Regression tests for shell scripts that derive SCRIPT_DIR from BASH_SOURCE.

When a script is executed via ``curl ... | bash`` it is read from stdin, so the
``BASH_SOURCE`` array is empty. Under ``set -u`` an unguarded ``${BASH_SOURCE[0]}``
reference is then an "unbound variable" error (see issue #37). These tests pipe the
``SCRIPT_DIR=`` assignment from each script into bash via stdin to reproduce that
exact condition and assert it stays clean.
"""

from __future__ import annotations

import pathlib
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

SCRIPTS = [
    "packaging/scripts/setup-usb.sh",
    "docs/vendor/convert.sh",
    "docs/vendor/fetch.sh",
    ".devcontainer/scripts/post-create.sh",
    ".devcontainer/scripts/post-attach.sh",
    ".devcontainer/scripts/initialize.sh",
    ".devcontainer/scripts/version-check.sh",
]


def _script_dir_line(script: str) -> str:
    text = (REPO_ROOT / script).read_text()
    for line in text.splitlines():
        if line.strip().startswith("SCRIPT_DIR="):
            return line
    raise AssertionError(f"no SCRIPT_DIR= assignment found in {script}")


@pytest.mark.parametrize("script", SCRIPTS)
def test_script_dir_safe_when_piped(script: str) -> None:
    """The SCRIPT_DIR assignment must not fail when bash reads from stdin."""
    line = _script_dir_line(script)
    snippet = f'set -euo pipefail\n{line}\necho "$SCRIPT_DIR"\n'

    # ``bash -s`` with input mimics ``curl | bash``: BASH_SOURCE is empty.
    result = subprocess.run(
        ["bash", "-s"],
        input=snippet,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert "unbound variable" not in result.stderr, result.stderr
    assert result.returncode == 0, result.stderr
