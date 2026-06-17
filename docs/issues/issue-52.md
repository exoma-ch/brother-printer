---
type: issue
state: open
created: 2026-06-17T18:06:28Z
updated: 2026-06-17T18:06:28Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/52
comments: 0
labels: chore, area:ci
assignees: none
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-17T18:22:39.083Z
---

# [Issue 52]: [chore: derive package version from git tag (hatch-vcs)](https://github.com/exoma-ch/brother-printer/issues/52)

## Problem

Both packages hardcode their version: `version = "0.1.0"` in each `pyproject.toml`, and `__version__ = "0.1.0"` in `brother_ptouch_driver/__init__.py`. Both CLIs surface this to users through `@click.version_option(package_name=...)`, which reads installed package metadata.

The shipped, CHANGELOG-driven release workflow tags `X.Y.Z` but **never updates these strings**, so after a release `brother-ptouch-driver --version` / `brother-ptouch-label --version` would keep reporting the previous version (e.g. `0.1.0` after a `0.2.0` release). This blocks cutting 0.2.0 cleanly.

## Fix

Derive the version from the git release tag via **hatch-vcs**, so the tag the release workflow already creates is the single source of truth (lockstep across both packages, matching today's de-facto model):

- Both packages declare `dynamic = ["version"]`, add `hatch-vcs` to build requires, and configure `[tool.hatch.version] source = "vcs"` with `raw-options = { root = "../.." }` (packages live in subdirs of the git root).
- `brother_ptouch_driver.__version__` reads `importlib.metadata.version(...)` instead of a literal.
- `uv.lock` regenerated (members become `dynamic`); `test_version` updated to compare against installed metadata rather than a hardcoded string.

Off-tag builds report a dev version (e.g. `0.2.1.devN+g<sha>`); a clean `X.Y.Z` is reported only at the exact tag.

Implemented in the PR linked below; unblocks the 0.2.0 release.
