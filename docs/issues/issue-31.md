---
type: issue
state: closed
created: 2026-06-04T15:35:56Z
updated: 2026-06-05T07:29:57Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/31
comments: 1
labels: chore, priority:low, area:testing, area:imaging, effort:small
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:47.560Z
---

# [Issue 31]: [[CHORE] Add tests for uncovered logic branches (raster downscale, monochrome modes, text alignment)](https://github.com/exoma-ch/brother-printer/issues/31)

**Chore Type:** General task

## Description

Coverage currently sits at 94% (252 passed, 10 skipped). Most of the 64 missing lines are defensive guards or hardware (pyusb) error paths, but a few are genuine logic branches that transform output and are currently untested. This issue tracks adding tests for those high-value gaps.

## Acceptance Criteria

- [ ] `imaging/raster.py` downscale path (`resize_to_tape_width`, lines 75-83) tested for both integer-factor and non-integer resample cases (`height > target_height`)
- [ ] `imaging/raster.py` `to_monochrome` mode branches covered: mode `"1"` passthrough (25-26) and catch-all `else` convert (27-28)
- [ ] `text.py` `_apply_fixed_width` alignment branches covered: `width == fixed_width` short-circuit (293), `left` (297), and `right` (299)
- [ ] Cheap validation guards covered with `pytest.raises` where reasonable (raster 47-48/98-99, text 67-68/118-119/123-124/145/334-335)
- [ ] TDD compliance (see .cursor/rules/tdd.mdc)

## Implementation Notes

Target test files: `packages/brother_ptouch_driver/tests/imaging/test_raster.py` and `packages/brother_ptouch_label/tests/test_text.py`.

Priority gap is the raster downscale path — existing tests only exercise upscaling (`height < target_height`), so the `height > target_height` branches that resize output are never run.

Explicitly out of scope (low value / high cost): `transport/usb.py` USBError mapping and CLI `sys.exit` paths requiring pyusb mocking; `raster.py` print-area-overflow guard (110-111) is likely unreachable with a valid `TapeWidth`.

## Related Issues

Related to #11 (v0.1.0 release prep).

## Priority

Low

## Changelog Category

No changelog needed
---

# [Comment #1]() by [c-vigo]()

_Posted on June 5, 2026 at 07:29 AM_

Closed via merged PR #32.

