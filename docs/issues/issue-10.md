---
type: issue
state: closed
created: 2026-05-28T15:21:06Z
updated: 2026-06-05T11:54:22Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/10
comments: 2
labels: chore, priority:medium, area:docs, effort:small
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:50.817Z
---

# [Issue 10]: [[CHORE] v0.1.0 release prep: README, packaging, and smoke test checklist](https://github.com/exoma-ch/brother-printer/issues/10)

## Description

Prepare v0.1.0 release: documentation, packaging, changelog, and manual hardware smoke test checklist.

## Problem Statement

Once core functionality is implemented, users need a documented quick-start path and a verified release artifact.

## Acceptance Criteria

- [ ] `README.md` with: project overview, installation (`pip install` / `uv sync`), quick-start example, supported hardware
- [ ] udev rules snippet for non-root USB access on Linux
- [ ] `CHANGELOG.md` entry for v0.1.0 listing all shipped features
- [ ] Console entry point `brother-printer` wired in `pyproject.toml` `[project.scripts]`
- [ ] Runtime dependencies declared: `pyusb`, `Pillow`, CLI framework
- [ ] Manual hardware smoke test checklist:
  - [ ] `discover` finds PT-E920BT
  - [ ] `status` shows correct tape width
  - [ ] Print QR PNG on 12mm tape with auto-cut
  - [ ] Print with `--no-cut`
  - [ ] Tape mismatch rejection works
- [ ] Tag and release v0.1.0 via existing release workflow

## Implementation Notes

- Depends on all feature issues (#4–#8) being complete
- Distribution: PyPI initially; container image deferred
- No built-in QR generation in v0.1 (user supplies PNG)

## Related Issues

- Depends on #1–#8, #9
- Part of v0.1 roadmap epic

## Priority

Medium — final milestone gate

---

# [Comment #1]() by [c-vigo]()

_Posted on May 28, 2026 at 03:21 PM_

Part of v0.1 roadmap epic #11

---

# [Comment #2]() by [c-vigo]()

_Posted on June 5, 2026 at 11:54 AM_

Docs prep merged in #33: README, CONTRIBUTING.md, CHANGELOG consolidation, setup-usb.sh, and just CLI/setup recipes. Remaining v0.1 release items (PyPI packaging, hardware smoke test checklist, version cut/tag) tracked separately.

