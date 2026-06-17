---
type: issue
state: open
created: 2026-06-17T13:02:40Z
updated: 2026-06-17T13:02:40Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/45
comments: 0
labels: feature
assignees: none
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-17T18:22:39.679Z
---

# [Issue 45]: [[FEATURE] Replicate label text across the tape for cable-wrap "flag" labels](https://github.com/exoma-ch/brother-printer/issues/45)

### Description

Add a `--replicate N` option (alias `--repeat`) to `brother-ptouch-label` that renders the label text **N times, tiled along the axis perpendicular to the text's reading direction**. This produces a single label whose text repeats across the tape so it can be wrapped around a cable and read from any rotation — the classic "cable-wrap / flag" label, especially useful on Brother flexible-ID (TZe-FX) tapes.

### Problem Statement

Today each label renders the text once. To label a cable so it's legible after wrapping, you must guess where the readable face lands, or print several separate labels. There is no built-in way to repeat the text across the tape to guarantee a readable face wherever the wrap ends up.

### Proposed Solution

A new option on `brother-ptouch-label`:

```
--replicate N    Repeat the rendered text N times, tiled perpendicular to the
                 text reading direction (default: 1). Alias: --repeat.
```

Behavior (replication is always perpendicular to the text baseline):

- **Without `--rotate`** — text reads along the tape length; the N copies stack across the tape **width** (Y-axis). Bounded by the physical tape, so each copy auto-fits to ~`print_area_pins / N` (reusing `max_font_size()`), with an optional small gap between copies. Validate that N copies remain legible / fit; error clearly otherwise.
- **With `--rotate`** — text reads across the width; the N copies repeat along the tape **length** (X-axis), which is unbounded. Require either `--width` (fixed feed length, already supported as `fixed_width`) or the explicit `--replicate N` count to bound the output. If `--width` is given without a count, fill the width with as many copies as fit.

Implementation sketch (isolated to the label package):
- Render one "unit" copy, then tile it `N` times along the appropriate axis before returning from `render_text()` in `packages/brother_ptouch_label/src/brother_ptouch_label/text.py`.
- Reuse `max_font_size()`, `_block_height()`, `_draw_stacked_lines()`, and `_apply_fixed_width()`.
- Add the `--replicate/--repeat` Click option and thread it through `render_kwargs` in `packages/brother_ptouch_label/src/brother_ptouch_label/cli/main.py`.
- Default `N=1` keeps current behavior byte-for-byte (backward compatible).

Example:

```
brother-ptouch-label "PWR-01" --tape 12mm --replicate 3 -o flag.png
```

### Alternatives Considered

- **Use `--copies`** — prints N *separate* labels, not one wrappable strip. Doesn't solve legibility-after-wrap.
- **Manual multi-line / pre-built image** — works but is tedious and doesn't auto-fit the font to the per-copy band.
- **`--wrap` auto-fill flag** (no count; fit as many copies as the tape allows) — viable ergonomic alternative; could be combined with `--replicate` (count overrides auto-fill). Open design question for implementation.
- **Flag-fold mirror mode** (two copies, second mirrored, for back-to-back flag tails) — a related but distinct feature; out of scope here, could be a follow-up.

### Additional Context

- Rendering orientation model: image Y-axis = tape width (`print_area_pins`), X-axis = feed/length; `--rotate` (`_render_rotated_90`) swaps the reading direction.
- Adjacent issue: #41 (confine print area on self-laminating tape) — independent.
- Brother's own software offers a comparable "cable wrap / repeat text" function for flexible-ID tapes.

### Impact

- **Who benefits:** anyone labeling cables/wires; flexible-ID (TZe-FX) tape users.
- **Compatibility:** backward compatible — new opt-in option, default `N=1` is a no-op.
- **Scope:** label package only (rendering + CLI); no driver/protocol changes.

### Changelog Category

Added

