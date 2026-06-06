---
type: issue
state: closed
created: 2026-06-01T11:22:37Z
updated: 2026-06-04T15:15:45Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/18
comments: 0
labels: refactor, priority:medium, area:cli, effort:small
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:50.013Z
---

# [Issue 18]: [[REFACTOR] Route discover CLI through library API per ADR-0002](https://github.com/exoma-ch/brother-printer/issues/18)

### Description

The `discover` CLI command imports directly from `brother_printer.transport`, which violates [ADR-0002](docs/adr/0002-architecture.md):

> **CLI** orchestrates via the library API. It must not import `transport` or `protocol` directly.

Current violations in `src/brother_printer/cli/main.py`:

```python
from brother_printer.transport import discover
from brother_printer.transport.errors import TransportError
```

The library API already exposes `discover_printers` (alias of `discover`) in `src/brother_printer/__init__.py`, but the CLI does not use it. `TransportError` is not re-exported at the library surface, which forces the CLI to reach into `transport.errors`.

### Files / Modules in Scope

- `src/brother_printer/cli/main.py`
- `src/brother_printer/__init__.py` (re-export discovery errors needed by CLI)
- `tests/cli/test_discover_command.py` (update mocks/imports to target library API bindings)

### Out of Scope

- Refactoring `brother_printer.printing` or library-internal imports from `transport`/`protocol` (allowed by ADR)
- Adding print/status CLI commands (#7, #8)
- Changing discover behavior, output format, or exit codes

### Invariants / Constraints

- All existing tests pass without behavior change
- `brother-printer discover` output and exit codes unchanged
- ADR-0002 layer rule: CLI must not import `transport` or `protocol` directly

### Acceptance Criteria

- [ ] `cli/main.py` imports `discover_printers` (and any needed error types) from `brother_printer` only — no `brother_printer.transport` or `brother_printer.protocol` imports
- [ ] Library API re-exports error types the CLI needs for discover (e.g. `TransportError`, `PermissionDeniedError`) via `__all__`
- [ ] CLI discover tests patch/mock via the library API import path used by `main.py`
- [ ] All existing tests pass
- [ ] No new warnings or linter errors
- [ ] TDD compliance (see `.cursor/rules/tdd.mdc`) — add or adjust a test that fails if CLI imports `transport`/`protocol` directly (e.g. import guard or updated mock paths written test-first)

### Changelog Category

No changelog needed

### Additional Context

ADR-0002 defines `discover_printers` as an example library API callable. Fixing discover now establishes the pattern before #7/#8 add more CLI commands.
