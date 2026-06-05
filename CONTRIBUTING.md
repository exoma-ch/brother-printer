# Contributing

Thank you for contributing to brother-printer. This document covers development
setup and workflow. For end-user installation and usage, see [README.md](README.md).

## Development environment

The recommended setup is the project devcontainer (VS Code or compatible IDE).
It includes Python 3.12, `uv`, `just`, pre-commit hooks, and USB passthrough
for hardware testing.

After cloning, sync all workspace packages and dev dependencies:

```bash
just sync
# equivalent: uv sync --all-packages --all-extras --all-groups
```

## Project layout

This repository is a **uv workspace** with two packages under `packages/`:

| Directory | Package | Import |
| --- | --- | --- |
| `packages/brother_ptouch_driver/` | `brother-ptouch-driver` | `brother_ptouch_driver` |
| `packages/brother_ptouch_label/` | `brother-ptouch-label` | `brother_ptouch_label` |

The repo root holds workspace-level config (`pyproject.toml`, pytest, coverage)
but is not itself a publishable package.

Architecture decisions are recorded in:

- [docs/adr/0002-architecture.md](docs/adr/0002-architecture.md) — five-layer
  design (transport, protocol, imaging, library API, CLI)
- [docs/adr/0003-driver-text-decoupling.md](docs/adr/0003-driver-text-decoupling.md)
  — driver/label package split and image-height contract

Vendor reference material lives under [docs/vendor/](docs/vendor/).

## Common tasks

| Command | Purpose |
| --- | --- |
| `just lint` | Run ruff linter |
| `just format` | Format code with ruff |
| `just precommit` | Run all pre-commit hooks |
| `just test` | Run pytest (hardware tests skipped) |
| `just test-cov` | Run pytest with coverage report |
| `just test-driver` | Run driver package tests only |
| `just test-label` | Run label package tests only |
| `just test-hardware` | Opt-in hardware tests (requires connected PT-E920BT) |
| `just test-connect` | Non-destructive hardware checks (no tape consumed) |
| `just test-print` | Tape-consuming hardware print matrix |
| `just test-all` | Full suite including hardware tests |
| `just gen-fixtures-driver` | Regenerate driver hardware PNG fixtures |
| `just gen-fixtures-labels` | Regenerate label golden PNG fixtures |
| `just discover` | List connected PT-E920BT printers |

## Testing

See [TESTING.md](TESTING.md) for the full test guide: suite layout, golden files,
hardware print matrix, tape prerequisites, and coverage gaps.

Hardware tests require a physically connected PT-E920BT and are opt-in via
`BROTHER_PTOUCH_DRIVER_HARDWARE=1` (set automatically by `just test-hardware`).
They never run during CI or a normal `just test`.

When adding features, follow test-driven development:
[.cursor/rules/tdd.mdc](.cursor/rules/tdd.mdc).

## Workflow standards

| Topic | Canonical reference |
| --- | --- |
| Commit messages | [docs/COMMIT_MESSAGE_STANDARD.md](docs/COMMIT_MESSAGE_STANDARD.md) |
| Branch naming | [.cursor/rules/branch-naming.mdc](.cursor/rules/branch-naming.mdc) |
| Changelog updates | [.cursor/rules/changelog.mdc](.cursor/rules/changelog.mdc) |
| Coding principles | [.cursor/rules/coding-principles.mdc](.cursor/rules/coding-principles.mdc) |

## Pull requests

Use the [pull request template](.github/pull_request_template.md). Ensure CI
passes (`just lint`, `just test`) and update [CHANGELOG.md](CHANGELOG.md) under
`## Unreleased` when your change has user-visible impact.

## Linux USB and hardware testing

USB setup, udev rules, and devcontainer passthrough are documented in
[docs/install/linux-usb.md](docs/install/linux-usb.md).
