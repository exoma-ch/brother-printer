---
type: issue
state: open
created: 2026-06-17T13:34:04Z
updated: 2026-06-17T13:45:47Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/50
comments: 0
labels: bug, priority:medium, area:imaging, effort:medium, semver:patch
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-17T18:22:39.380Z
---

# [Issue 50]: [[BUG] Self-laminating printable band is not a fixed height — varies by tape width](https://github.com/exoma-ch/brother-printer/issues/50)

### Description

The self-laminating printable-band feature merged in #41 / PR #47 assumes the printable white strip is a **fixed physical height** (~9.8 mm ≈ 140 px at 360 dpi) for **all** tape widths. Hardware testing on a PT-E920BT shows this assumption is wrong: the band height **varies with tape width**, and there is also a small vertical-offset issue on 24 mm.

This is a regression in the just-merged feature (currently on `main`): on wider self-laminating tape, content is confined to far less than the actual printable strip.

### Observed (PT-E920BT hardware)

| Tape | Actual printable strip | Current code (140 px) | Notes |
| --- | --- | --- | --- |
| 24 mm | ~9.8 mm (~139 px) | 140 px | Content sits **slightly too low**; ~**136 px** looks better (pending verification) |
| 36 mm (TZe-SL261) | ~**15 mm** (~213 px) | 140 px | Band is **too short** — only ~9.8 mm of a ~15 mm strip is used |

So the band is **not** bounded by a single fixed physical height; it scales with the tape. The original reasoning (min cable circumference → fixed ~9.8 mm) does not hold across widths.

### Expected

The printable band height should be a **per-tape-width** value (like `print_area_pins`), measured per cartridge, e.g. roughly:
- 24 mm → ~136–139 px (~9.6–9.8 mm)
- 36 mm → ~213 px (~15 mm)

Vertical placement should also be re-checked on 24 mm (content appears shifted toward the flap edge at 140 px).

### Steps to reproduce

1. Load self-laminating tape (e.g. 24 mm TZe-SL2xx, or 36 mm TZe-SL261).
2. `brother-ptouch-label "Self-laminating\n Cable diam. 3.0 to 10.4mm"`
3. Observe the printed text does not fill / align to the actual white strip (too short on 36 mm; slightly low on 24 mm).

### Proposed fix

- Replace the single `self_laminating_band_pins()` / `SELF_LAMINATING_BAND_PINS` constant with a **per-`TapeWidth` band table** (mirroring `_TAPE_WIDTH_PINS`), populated from hardware measurement; `effective_print_pins()` looks up by width.
- Update `info tapes` to show the per-width self-laminating band (or a column) instead of one fixed row.
- Re-verify vertical anchoring/centering on 24 mm.
- Only 24 mm and 36 mm are measurable here; other widths need measurement or a documented best-effort interpolation.

### Additional context

- Introduced by #41 (PR #47). Builds on the media detection from #39.
- Band geometry lives in `packages/brother_ptouch_driver/src/brother_ptouch_driver/protocol/enums.py` (`self_laminating_band_pins`, `effective_print_pins`); see also `docs/vendor/tze-tape-widths.md`.

### Changelog Category

Fixed

### Follow-up to confirm during testing

When testing the 24 mm tape, also verify which bytes the **24 mm self-laminating** cartridge actually reports. The 24 mm tape on hand during triage identified as **Flexible ID** (media `0x14`, colour `0x90` `WHITE_FLEX_ID`), so `is_self_laminating` returned `False` and no band was applied (effective height 320 px). Need to confirm whether that was simply a different (Flexible ID) cartridge or whether the 24 mm SL cartridge reports SL/`0x80` at all — this affects whether detection needs widening.
