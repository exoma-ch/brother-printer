---
type: issue
state: closed
created: 2026-06-03T11:58:12Z
updated: 2026-06-04T13:44:53Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/25
comments: 1
labels: feature, priority:medium, area:imaging, area:cli, effort:medium, semver:minor
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:48.338Z
---

# [Issue 25]: [[FEATURE] Direct text printing (font size, orientation, multi-line) with max-font-size helper](https://github.com/exoma-ch/brother-printer/issues/25)

## Description

Add first-class support for printing plain text directly, without first
producing an image file. Users supply a string and the library renders it
to a monochrome bitmap sized for the loaded tape, then reuses the existing
`image_to_raster` -> `encode_job` -> transport path.

Includes:
- Configurable **font size** (explicit px, or auto-fit to the tape height).
- **Orientation** (reuse the existing 0/90/180/270 rotation in the raster pipeline).
- **Multi-line** text (newline-separated, with per-line alignment).
- A **helper to compute the maximum font size** that fits a given number of
  lines on a given tape width.

## Problem Statement

Today the only way to print a label is to provide an image file (`print`
command takes image paths or a `--csv`). Printing a simple text label means
the user must open an external editor, render text to an image at the right
pixel height for the tape, and export a file. This is the single most common
label-maker use case and is currently unsupported end to end.

## Proposed Solution

Add a text-rendering module in the imaging layer and surface it through the
library API and CLI.

1. **`imaging/text.py`** — `render_text(...) -> PIL.Image.Image`
   - Inputs: `text` (supports `\n` for multi-line), `tape_width: TapeWidth`,
     optional `font_path`, optional `font_size` (px), `align`
     (left/center/right), `line_spacing`, `rotate`, `margin`.
   - Renders a 1-bit/`L` image whose height matches
     `tape_width.print_area_pins`; width grows to fit content (or a fixed
     `--width`).
   - When `font_size` is omitted, auto-fit using the helper below
     (ptouch-style "fill ~the tape height").
   - Falls back to `PIL.ImageFont.load_default()` when no font is given.

2. **`max_font_size(...)` helper** (in `imaging/text.py`, re-exported)
   - Signature sketch:
     `max_font_size(tape_width: TapeWidth, lines: int, *, line_spacing: float = 0.0, font_path: str | None = None) -> int`
   - Computes the largest font size (px) such that `lines` lines plus spacing
     fit within `tape_width.print_area_pins`. Uses font metrics
     (`ImageFont.getbbox`/ascent+descent) when a TTF is given, else a
     conservative ratio for the default bitmap font.
   - Pure function, no I/O — easy to unit test against known pin counts.

3. **Library API** — add `print_text(text, tape_width, **opts)` to
   `printing.py` (compose `render_text` + `print_image`) and re-export
   `render_text`, `max_font_size`, `print_text` from
   `brother_printer/__init__.py`.

4. **CLI** — extend the existing `print` command with:
   `--text`, `--font PATH`, `--font-size PX`, `--align`, `--rotate`,
   and multi-line from `\n`. Mirrors `nbuchwitz/ptouch` flags
   (`--font`, `--font-size`, `--align`).

## Alternatives Considered

- **Protocol-level text/internal printer fonts** — the P-touch raster protocol
  in this repo is image/raster only; the printer is not driven via built-in
  fonts here. Rejected: would bypass the established image-first architecture
  (ADR-0002) and the validated raster path.
- **Require users to pre-render images** (status quo) — high friction for the
  most common use case.
- **Add a heavy text layout dependency (pango/cairo)** — overkill; Pillow's
  `ImageFont`/`ImageDraw` (already a dependency) is sufficient for single-style
  labels.

## Additional Context

Inspiration from existing open-source P-touch tooling:
- `nbuchwitz/ptouch` — `TextLabel`, auto-size to ~80% of print height,
  `auto_size=False` to respect a fixed font size, CLI `--font/--font-size/--align`.
- `pklaus/brother_ql` and forks (`brother-label`, `brother-ql2`) — image-based
  raster pipeline with text rendered via Pillow, "scaled to fit the width".

Integration points already in place:
- `imaging.image_to_raster(image, tape_width, rotate=..., margin=..., allow_distortion=...)`
  — note `allow_distortion=True` may be needed for arbitrary text heights since
  non-integer scale factors raise `ImageScalingError`.
- `TapeWidth.print_area_pins` gives the printable pixel height per tape.

## Impact

- Who benefits: anyone making text labels (the primary label-maker workflow).
- Backward compatible: purely additive (new module, new API function, new CLI
  flags). No changes to existing image/CSV printing.
- New runtime code paths only; `pillow` already required, so no new dependency.

## Acceptance criteria

- [ ] `render_text` produces a monochrome image at the correct tape pixel height.
- [ ] Multi-line text renders with configurable alignment and spacing.
- [ ] `--font-size` respected; omitting it auto-fits via `max_font_size`.
- [ ] Orientation (rotate) supported and matches existing raster rotation.
- [ ] `max_font_size(tape_width, lines)` returns sizes that fit within
      `print_area_pins` (verified for representative tapes/line counts).
- [ ] CLI can print a text label end to end (mocked transport in tests).
- [ ] TDD compliance (see .cursor/rules/tdd.mdc)

## Changelog Category

Added

---

# [Comment #1]() by [c-vigo]()

_Posted on June 4, 2026 at 01:44 PM_

Resolved by #28 (merged into `dev`). Direct text printing shipped via the new `brother-ptouch-label` package and CLI.

