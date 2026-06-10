---
type: issue
state: open
created: 2026-06-09T14:08:40Z
updated: 2026-06-09T14:21:52Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/37
comments: 1
labels: bug
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-10T06:25:48.583Z
---

# [Issue 37]: [[BUG] setup-usb.sh fails with 'BASH_SOURCE[0]: unbound variable' when run via curl | bash](https://github.com/exoma-ch/brother-printer/issues/37)

## Description

When `packaging/scripts/setup-usb.sh` is run the documented way (`curl -fsSL .../setup-usb.sh | bash`), it prints `bash: line 15: BASH_SOURCE[0]: unbound variable` on the very first line.

Root cause: line 11 enables `set -euo pipefail` (nounset), and line 15 references `${BASH_SOURCE[0]}` without a default:

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
```

When bash reads the script from stdin (`curl | bash`), there is no source file, so the `BASH_SOURCE` array is empty and `${BASH_SOURCE[0]}` is an unbound reference under `set -u`. The error is currently swallowed because it occurs inside a command substitution (`SCRIPT_DIR` ends up empty, the local-rule lookup misses, and it falls back to fetching the udev rule from GitHub), so the run still completes — but it is a real bug on the primary install path.

The same `${BASH_SOURCE[0]}` pattern (no default) also exists in `docs/vendor/convert.sh`, `docs/vendor/fetch.sh`, `.devcontainer/scripts/post-create.sh`, `.devcontainer/scripts/post-attach.sh`, `.devcontainer/scripts/initialize.sh`, and `.devcontainer/scripts/version-check.sh`. Those are safe in practice (always run as files), but should be hardened for consistency.

## Steps to Reproduce

1. On a fresh machine, run: `curl -fsSL https://raw.githubusercontent.com/exoma-ch/brother-printer/main/packaging/scripts/setup-usb.sh | bash`
2. Observe the first line of output.

Minimal hermetic reproduction (no sudo/network):

```bash
printf 'set -euo pipefail\n%s\necho "$SCRIPT_DIR"\n' \
  'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"' | bash
```

## Expected Behavior

The script runs cleanly via `curl | bash` with no `unbound variable` error, correctly falling back to fetching the udev rule from GitHub when no local checkout is present.

## Actual Behavior

```
bash: line 15: BASH_SOURCE[0]: unbound variable
```

is printed on the first line before the rest of the setup proceeds.

## Environment

- **OS**: Ubuntu (reported on a fresh `exopet-pc-dev` host)
- **Shell**: bash (via `curl | bash`, i.e. reading the script from stdin)
- **Image Version/Tag**: main branch of the script
- **Architecture**: AMD64

## Additional Context

Affects the primary, documented install path (`curl ... | bash`). The bug is masked today by command-substitution error swallowing, making it fragile rather than benign.

## Possible Solution

Give `BASH_SOURCE[0]` a default so it is safe under `set -u`:

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
```

When piped, `$0` is `bash`, `dirname` yields `.`, `SCRIPT_DIR` becomes the cwd, the local-rule lookup misses, and it falls back to the URL (intended standalone behavior, now without the error). Behavior when run as a file is unchanged. Apply the same fix to the other six scripts listed above.

## Changelog Category

Fixed
---

# [Comment #1]() by [c-vigo]()

_Posted on June 9, 2026 at 02:09 PM_

## Implementation plan

### Fix

Give `BASH_SOURCE[0]` a default so it is safe under `set -u` when piped:

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
```

Apply to all scripts using the same pattern:
- `packaging/scripts/setup-usb.sh` (line 15) — the actual bug, documented for `curl | bash`
- `docs/vendor/convert.sh` (line 7)
- `docs/vendor/fetch.sh` (line 7)
- `.devcontainer/scripts/post-create.sh` (line 17)
- `.devcontainer/scripts/post-attach.sh` (line 15)
- `.devcontainer/scripts/initialize.sh` (line 10)
- `.devcontainer/scripts/version-check.sh` (line 29)

### Workflow / conventions

Needs a `bugfix/37-bash-source-unbound` branch off `dev` (the `no-commit-to-branch` pre-commit hook blocks committing on `dev`), with TDD commits referencing `Refs: #37`.

1. `gh issue develop 37 --base dev --name bugfix/37-bash-source-unbound --checkout`
2. **TDD red**: add the regression test, confirm it fails on current code, commit (`test: ...`, `Refs: #37`).
3. **TDD green**: apply the `${BASH_SOURCE[0]:-$0}` fix to all 7 scripts, confirm the test passes, commit (`fix: ...`, `Refs: #37`).
4. Update `CHANGELOG.md` Unreleased -> `### Fixed`, commit.
5. Run `just precommit` (shellcheck) and `just test`.

### Regression test design

The repo has no shell test harness and `testpaths` in `pyproject.toml` only includes the two packages. Add `packaging/tests/test_setup_usb.py` and register `"packaging/tests"` in `[tool.pytest.ini_options].testpaths`.

The test reproduces the exact failure hermetically (no sudo/network): for each affected script it extracts the `SCRIPT_DIR=...` line and runs it via stdin to mimic `curl | bash`:

```python
import subprocess, pathlib, pytest

SCRIPTS = [
    "packaging/scripts/setup-usb.sh",
    "docs/vendor/convert.sh",
    "docs/vendor/fetch.sh",
    ".devcontainer/scripts/post-create.sh",
    ".devcontainer/scripts/post-attach.sh",
    ".devcontainer/scripts/initialize.sh",
    ".devcontainer/scripts/version-check.sh",
]

@pytest.mark.parametrize("script", SCRIPTS)
def test_script_dir_safe_when_piped(script):
    text = pathlib.Path(script).read_text()
    line = next(l for l in text.splitlines() if l.strip().startswith("SCRIPT_DIR="))
    snippet = f"set -euo pipefail\n{line}\necho \"$SCRIPT_DIR\"\n"
    # No first arg -> bash reading from stdin leaves BASH_SOURCE empty (curl | bash)
    r = subprocess.run(["bash", "-s"], input=snippet, capture_output=True, text=True)
    assert "unbound variable" not in r.stderr
    assert r.returncode == 0
```

This fails on current code (proving the bug) and passes after the fix, guarding all 7 scripts against regression.

### Verification
- `just test` (new test passes; existing suite unaffected)
- `just precommit` (shellcheck clean; the fix is shellcheck-safe)
- Manual smoke: pipe the fixed `SCRIPT_DIR=...` line into `bash` and confirm it prints the cwd with no error

