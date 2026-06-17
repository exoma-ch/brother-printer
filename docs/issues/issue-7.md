---
type: issue
state: closed
created: 2026-05-28T15:20:55Z
updated: 2026-06-02T14:10:41Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/7
comments: 1
labels: feature, priority:high, area:cli, effort:small, semver:minor
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:52.080Z
---

# [Issue 7]: [[FEATURE] CLI print command with tape selection and auto-cut](https://github.com/exoma-ch/brother-printer/issues/7)

## Description

Implement the main `brother-printer print` CLI command: print an image file on PT-E920BT with tape selection, auto-cut control, and safety checks.

## Problem Statement

Users need a command-line workflow to print QR code PNGs (and other images) without Brother's proprietary software.

## Proposed Solution

```
brother-printer print PATH --tape {3.5|6|9|12|18|24|36}mm [--auto-cut|--no-cut] [--copies N] [--threshold T] [--rotate DEG] [--margin PX] [--printer ID]
```

Orchestrates: transport → status check → imaging → protocol encode → send.

## Acceptance Criteria

- [ ] `brother-printer print image.png --tape 12mm` prints on connected PT-E920BT
- [ ] `--auto-cut` (default) and `--no-cut` flags control cutting behavior
- [ ] `--copies N` prints multiple copies
- [ ] `--threshold`, `--rotate`, `--margin` passed through to imaging layer
- [ ] Refuse to print if requested tape width does not match printer status reply (safety)
- [ ] Clear error messages for common failures (no printer, wrong tape, permission denied)
- [ ] Console entry point registered in `pyproject.toml`

## Implementation Notes

- Use Click or argparse (match project convention)
- Thin CLI layer; all logic in library API
- Depends on #4 (transport), #5 (protocol), #6 (imaging)

## Related Issues

- Depends on #4, #5, #6
- Part of v0.1 roadmap epic

## Priority

High

---

# [Comment #1]() by [c-vigo]()

_Posted on May 28, 2026 at 03:21 PM_

Part of v0.1 roadmap epic #11

