---
type: issue
state: closed
created: 2026-06-17T12:42:10Z
updated: 2026-06-17T13:28:35Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/41
comments: 0
labels: feature, priority:medium, area:imaging, area:cli, effort:medium, semver:minor
assignees: none
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-17T18:22:40.380Z
---

# [Issue 41]: [[FEATURE] Confine print area to the white band on self-laminating tape (PNG + text)](https://github.com/exoma-ch/brother-printer/issues/41)

### Description

When self-laminating tape is loaded, automatically confine the printable area to the narrow white strip at the edge of the tape and fit content within it — for **both** direct PNG printing (`brother-ptouch-driver print`) and rendered text (`brother-ptouch-label`) — instead of using the full tape width as today.

### Problem Statement

Self-laminating TZe-SL tapes have a printable white strip plus a clear laminate flap that wraps the cable. All print paths currently target the full tape width (`print_area_pins`), so content prints partly onto the clear flap and is misaligned. The only workaround is a hand-tuned text margin, e.g. `brother-ptouch-label --margin-bottom 200 "Self-laminating"`, and there is no equivalent for direct PNG printing.

### Proposed Solution

Implement the confinement once in the imaging layer (so PNG, text, and strip/CSV all benefit), and additionally render text at the band dimensions so it isn't just downscaled:

1. **Detect.** The status decoder recognizes `MediaType.SELF_LAMINATING (0x16)` (added in #39). `print_image`/`print_strip` already query status, so `status.media_type` is in hand.
2. **Band geometry.** The white strip is a *fixed physical height* (not a fraction of tape width), bounded by minimum cable circumference: min Ø 3.0 mm → ~9.5 mm → use **9.8 mm** ≈ **139 pins** at 360 dpi (`9.8 × 360 / 25.4`). Measured equal on 24 mm tape and 36 mm TZe-SL261; only the clear flap grows with tape width. Define a constant (e.g. `SELF_LAMINATING_BAND_MM = 9.8`) near the tape-geometry code and derive pins from it.
3. **Imaging layer (core).** Add an *effective print height* to the raster pipeline (`image_to_raster` / `resize_to_tape_width` / `pack_raster_lines`), defaulting to `print_area_pins`. When self-laminating, callers pass `band_pins`: the image is packed anchored at the white-strip edge — the existing `right_pins + row` offset already anchors there, so only the effective height changes. `print_image`/`print_strip` derive the effective height from `status.media_type`. The flap is left unprinted (**padded** — pins stay 0); the image occupies only the band rows. Fitting into the band uses the existing rule (supply a band-height image, or pass `--scale`) — no automatic downscaling, which would blur QR modules. A PNG already authored at band height packs unchanged.
4. **Text renderer (quality).** So text is sized for the band rather than downscaled, have the label renderer fit the font and center within `band_pins` (font auto-size and vertical centering in `text.py`). Surface `media_type` from the status query the label CLI already performs (`detect_tape_width`). This generalizes the manual `--margin-bottom` workaround into precise, automatic behavior.

Trigger is **auto-detect only**: no new CLI flag. Explicit `--margin-*` values, if supplied, still take precedence over the auto band.

### Alternatives Considered

- **Text-only fix in the renderer** (no imaging-layer change) — rejected; it would leave direct PNG printing unconfined and duplicate the band logic. Centralizing in the imaging layer covers PNG, text, and strip/CSV from one place.
- **Explicit `--self-laminating` flag** — rejected; the printer already reports the media type and the user wants it by default.
- **Per-tape-width band table** — unnecessary; the band is a fixed physical height across tape sizes.

### Additional Context / Open questions

- Strip orientation confirmed on 24 mm (white strip at the `right_pins`/row-0 edge, via the `--margin-bottom` workaround); re-verify on 36 mm TZe-SL261.
- **PNG fit semantics:** across the tape the flap is padded (left unprinted); within the band the existing rule applies — a non-band-height PNG errors unless `--scale` is passed, rather than auto-downscaling (which would blur QR modules). Confirm the error message points users at `--scale` / band-height authoring.
- **Rotation:** with `--rotate` (90°) the across-tape extent is the pre-rotation image *width*; the text renderer must clamp the correct axis. Needs explicit handling/tests.
- **Offline PNG preview** (`-o`, no printer) can't auto-detect media and won't get the band. Acceptable; a future explicit override could cover it.
- Depends on / builds upon #39 (`MediaType.SELF_LAMINATING` decoding).

### Impact

Backward-compatible (`semver:minor`): behavior changes only when self-laminating tape is detected; all other tapes render exactly as before. Benefits anyone labeling cables with self-laminating tape.

### Changelog Category

Added

