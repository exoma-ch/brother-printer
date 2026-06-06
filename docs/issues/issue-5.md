---
type: issue
state: closed
created: 2026-05-28T15:20:52Z
updated: 2026-05-29T08:48:33Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/5
comments: 1
labels: feature, priority:high, area:protocol, effort:large, semver:minor
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:52.881Z
---

# [Issue 5]: [[FEATURE] P-touch raster protocol encoder and status decoder](https://github.com/exoma-ch/brother-printer/issues/5)

## Description

Implement P-touch raster protocol encoder and 32-byte status reply decoder as pure functions (bytes in, bytes out).

## Problem Statement

Brother P-touch printers use a proprietary raster command protocol. We need to encode print jobs and decode printer status without coupling to transport or CLI layers.

## Proposed Solution

Pure-function modules in `src/brother_printer/protocol/`:
- **Encoder**: init, invalidate, status request, mode select, print information, advanced mode, margin, compression, raster lines, print, eject
- **Decoder**: parse 32-byte status reply (media type/width, error byte, phase, notification, tape color)

## Acceptance Criteria

- [ ] Encoder produces valid command byte streams for a minimal print job
- [ ] Decoder parses 32-byte status reply into typed dataclass/struct
- [ ] Tape width from status reply maps to TZe sizes (3.5–36 mm)
- [ ] Error byte decoded to human-readable error conditions
- [ ] Auto-cut flag encoded in print/eject commands
- [ ] All functions are pure (no I/O); transport layer sends/receives bytes
- [ ] Golden-file tests for known command sequences

## Implementation Notes

- Reference `docs/vendor/` command docs from #1 and ADR from #2
- ptouch-print source is primary prior-art for command sequences
- PT-E920BT is 360 dpi; ensure raster line packing matches spec

## Related Issues

- Depends on #1, #2, #3
- Blocks #6, #7, #8
- Part of v0.1 roadmap epic

## Priority

High

---

# [Comment #1]() by [c-vigo]()

_Posted on May 28, 2026 at 03:21 PM_

Part of v0.1 roadmap epic #11

