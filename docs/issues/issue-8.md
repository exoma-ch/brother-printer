---
type: issue
state: closed
created: 2026-05-28T15:21:02Z
updated: 2026-06-03T09:21:31Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/8
comments: 1
labels: feature, priority:medium, area:cli, effort:small, semver:minor
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:51.686Z
---

# [Issue 8]: [[FEATURE] CLI status and info tapes commands](https://github.com/exoma-ch/brother-printer/issues/8)

## Description

Implement `brother-printer status` and `brother-printer info tapes` CLI commands for printer diagnostics and tape reference.

## Problem Statement

Users need to verify printer connectivity, check loaded tape, and look up supported tape widths before printing.

## Proposed Solution

- `brother-printer status [--printer ID]` — query printer via status request, display media type/width, errors, firmware if available
- `brother-printer info tapes` — list supported TZe tape widths and printable pixel widths at 360 dpi

## Acceptance Criteria

- [ ] `status` sends status request and decodes 32-byte reply into human-readable output
- [ ] Shows: tape width, media type, error state, phase, tape color (if available)
- [ ] `info tapes` lists all supported widths: 3.5, 6, 9, 12, 18, 24, 36 mm with pixel dimensions
- [ ] Exit code non-zero on printer errors
- [ ] Works with `--printer ID` to target a specific device from `discover`

## Implementation Notes

- Thin CLI over protocol decoder (#5) and transport (#4)
- Can be implemented in parallel with #7 once #4 and #5 are done

## Related Issues

- Depends on #4, #5
- Part of v0.1 roadmap epic

## Priority

Medium

---

# [Comment #1]() by [c-vigo]()

_Posted on May 28, 2026 at 03:21 PM_

Part of v0.1 roadmap epic #11

