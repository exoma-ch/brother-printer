---
type: issue
state: closed
created: 2026-05-28T15:20:53Z
updated: 2026-06-01T10:42:21Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/6
comments: 1
labels: feature, priority:high, area:imaging, effort:medium, semver:minor
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:52.501Z
---

# [Issue 6]: [[FEATURE] Image-to-raster pipeline tuned for QR code quality](https://github.com/exoma-ch/brother-printer/issues/6)

## Description

Build an image-to-raster pipeline optimized for high-quality QR code printing: strict 1-bit conversion, integer scaling, tape-width-aware resize.

## Problem Statement

The primary v0.1 use case is printing pre-generated QR code PNGs. QR codes require pixel-perfect module boundaries — dithering and non-integer scaling cause unreadable codes.

## Proposed Solution

Module in `src/brother_printer/imaging/`:
- Input: PIL Image (any mode)
- Output: 1-bit raster lines matching tape printable width at 360 dpi
- Default: strict threshold (no dithering)
- Resize with nearest-neighbor; prefer integer upscaling factors
- Reject inputs whose aspect ratio would distort a square QR

## Acceptance Criteria

- [ ] Convert RGBA/RGB/grayscale PIL Image to 1-bit raster
- [ ] Tape-width-aware resize using printable pixel widths per TZe size
- [ ] `--threshold` configurable (default: strict, no dithering)
- [ ] `--rotate` support (0/90/180/270)
- [ ] `--margin` configurable padding in pixels
- [ ] Warn or reject when input dimensions would non-uniformly scale a square QR
- [ ] Unit tests with synthetic QR-like checkerboard patterns verifying module sharpness

## Implementation Notes

- Learn from brother_ql issue reports on barcode blurriness (threshold vs dither trade-offs)
- User generates QR PNG externally; this module only handles image → raster
- Depends on #3 (skeleton); protocol layer (#5) consumes raster output

## Related Issues

- Depends on #3
- Blocks #7
- Part of v0.1 roadmap epic

## Priority

High

---

# [Comment #1]() by [c-vigo]()

_Posted on May 28, 2026 at 03:21 PM_

Part of v0.1 roadmap epic #11

