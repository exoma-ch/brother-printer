---
type: issue
state: closed
created: 2026-06-04T12:19:22Z
updated: 2026-06-04T15:15:29Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/27
comments: 3
labels: refactor, priority:medium, area:testing, effort:medium
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:47.983Z
---

# [Issue 27]: [[REFACTOR] Refurbish hardware print tests with readable text+QR fixtures and negative-path coverage](https://github.com/exoma-ch/brother-printer/issues/27)

## Description

The opt-in hardware print suite (`packages/brother_printer/tests/hardware/`) prints meaningless QR squares whose only verification is "did the printer accept the bytes." Refurbish it so printed output is human-verifiable and the suite actively proves the safety guards, while realigning fixtures with the ADR-0003 driver/text split.

Specifically:
- Replace per-width `qr_*.png` fixtures with combined fixtures that print the **tape width as readable text** (e.g. "12 mm") plus a **compact QR** for fine-detail/sharpness coverage, optimized for contrast (strict 1-bit black/white). A human can confirm at a glance that the right fixture printed on the right tape.
- Add **negative-path** hardware tests that assert the existing guards instead of skipping: wrong tape width → `TapeMismatchError`; wrong image height with `scale=False` → `ImageScalingError`. Both raise before any raster bytes are written, so they consume **zero tape**.
- Keep the grayscale (`threshold`) and distort (`scale`) fixtures, which cover behaviors a tape-sized text label cannot.
- Close low-cost hardware coverage gaps noted in TESTING.md by exercising `print_png()` and `print_image(copies>1)` on the loaded tape.

## Files / Modules in Scope

- `packages/brother_printer/tests/hardware/assets/generate_fixtures.py` (standalone text+QR drawing; rename QR fixtures → label fixtures)
- `packages/brother_printer/tests/hardware/conftest.py` (fixture path mappings, helper fixtures)
- `packages/brother_printer/tests/hardware/test_print.py` (refresh P1/P3/P4, add negative-path tests, add `print_png`/`copies` coverage)
- `packages/brother_printer/tests/hardware/assets/*.png` (regenerated committed fixtures)
- `TESTING.md` (print matrix, fixture asset table, coverage-gaps table)
- `CHANGELOG.md` (`### Changed` entry)
- `pyproject.toml` dev group (keep `qrcode`, or swap to `segno` if true Micro QR is chosen)

## Out of Scope

- No changes to library/CLI production source under `packages/*/src/` (`printing.py`, `imaging/`, `protocol/`, `transport/`, `cli/`). This is a test/fixture refactor only.
- No changes to software (non-hardware) tests under `tests/protocol/`, `tests/imaging/`, `tests/transport/`, `tests/cli/`.
- No new public API, CLI flags, or error types (the negative tests assert guards that already exist).
- No change to the `BROTHER_PRINTER_HARDWARE=1` opt-in gating or markers.

## Invariants / Constraints

- Production behavior is unchanged; all existing software tests pass without modification.
- Hardware tests remain opt-in and skipped by default (`pytest.mark.hardware` + `skipif`).
- New fixtures keep height == `TapeWidth.print_area_pins` and stay rotatable (square canvas, integer scale factor 1) so P1 rotation cases remain lossless.
- Fixtures are pure 1-bit-friendly black/white (max contrast); the embedded QR stays scannable, or is omitted on the narrowest widths (3.5/6 mm) where it cannot render scannably.
- Negative-path tests consume **no tape** (assertions occur before any raster write).
- `just gen-test-images` remains the single regeneration entrypoint.

## Acceptance Criteria

- [ ] `generate_fixtures.py` produces per-width `label_{width}mm.png` with readable width text + compact QR + orientation marker, drawn with Pillow only (no `brother_printer_text` import).
- [ ] Committed fixtures regenerated via `just gen-test-images`; old `qr_*.png` removed.
- [ ] `conftest.py` and `test_print.py` reference the new fixtures; happy-path matrix (P0–P4) still passes on a matching loaded tape.
- [ ] New test asserts `TapeMismatchError` when printing with a width different from the loaded tape (zero tape consumed).
- [ ] New test asserts `ImageScalingError` when printing a wrong-height image with `scale=False` (zero tape consumed).
- [ ] `print_png()` happy path and `print_image(copies=2)` exercised on the loaded tape (closes TESTING.md gaps).
- [ ] `TESTING.md` print matrix, fixture-asset table, and coverage-gaps table updated.
- [ ] `CHANGELOG.md` `### Changed` entry added referencing this issue.
- [ ] No new linter errors; full `just test` (non-hardware) green.

## Changelog Category

Changed

## Additional Context

- ADR-0003 (driver/text decoupling): `docs/adr/0003-driver-text-decoupling.md`.
- Imaging sharpness rationale and pin tables: `docs/vendor/tze-tape-widths.md`, `packages/brother_printer/src/brother_printer/protocol/enums.py` (`_TAPE_WIDTH_PINS`).
- **Open decision:** keep compact standard QR (`qrcode`) vs switch to true Micro QR (`segno`). Default to compact standard QR unless reviewer prefers `segno`.
- Relates to hardware-test infra history: #4, #7, #22; supersedes the QR-fixture approach from #7.

---

# [Comment #1]() by [c-vigo]()

_Posted on June 4, 2026 at 12:19 PM_

## Suggested implementation plan

Follow TDD per `.cursor/rules/tdd.mdc`; branch `refactor/<n>-refurbish-hardware-fixtures` off `dev` per `.cursor/rules/branch-naming.mdc`.

### 1. Fixtures (config/asset change, TDD-exempt with note)

- Rewrite `generate_fixtures.py`: add `_render_label(width, *, size)` that draws:
  - (a) a top orientation bar,
  - (b) large `"{mm} mm"` text via `ImageFont.load_default(size=...)` sized to the available area,
  - (c) a compact QR in a corner (`box_size`/`border` tuned to min scannable module; omit when `size <= ~64`).
- Output `label_{width}mm.png`. Keep `_render_grayscale_gradient` and `_render_distort_source`.
- Run `just gen-test-images`; commit regenerated assets and removal of `qr_*.png`.

### 2. conftest

- Rename `_TAPE_FIXTURES` → `_LABEL_FIXTURES` mapping to `label_*`.
- Keep `_GRAY_FIXTURES` / `DISTORT_FIXTURE`; rename `fixture_path` fixture accordingly.

### 3. Negative-path tests (write failing first, commit `test:`)

- `test_print_wrong_tape_width_raises`: pick `wrong = next(w for w in TapeWidth if w != loaded_tape)`; `with pytest.raises(TapeMismatchError): print_image(img, wrong)`.
- `test_print_wrong_image_size_raises`: build image height `loaded_tape.print_area_pins + 1`; `with pytest.raises(ImageScalingError): print_image(img, loaded_tape)` (default `scale=False`).

### 4. Coverage-gap tests

- `test_print_png_round_trip`: `print_png(path.read_bytes(), loaded_tape)`.
- `test_print_copies`: `print_image(img, loaded_tape, copies=2)`.
- Assert `written > 0` and idle wait.

### 5. Refresh happy-path matrix

- Update P1/P4 to use new label fixtures; keep grayscale/distort cases.

### 6. Docs / changelog

- Update `TESTING.md` print matrix, fixture-asset table, coverage-gaps table.
- Add `CHANGELOG.md` `### Changed` entry referencing this issue.

### 7. Verify

- `just test` (non-hardware) green.
- On hardware: `just test-hardware` to confirm matrix + negative paths.


---

# [Comment #2]() by [c-vigo]()

_Posted on June 4, 2026 at 01:07 PM_

### Suggestion: add scoped hardware test recipes alongside this refactor

While refurbishing the hardware print suite, it would be convenient to split the opt-in hardware runs into intent-based `just` recipes in `justfile.project`, complementing the existing `test-hardware`:

- **`test-connect`** — non-destructive checks that require the printer but consume **no tape** (connectivity + status):

  ```
  BROTHER_PRINTER_HARDWARE=1 uv run pytest -m hardware \
    packages/brother_printer/tests/hardware/test_connectivity.py \
    packages/brother_printer/tests/hardware/test_status.py {{ args }}
  ```

- **`test-print`** — the tape-consuming print matrix:

  ```
  BROTHER_PRINTER_HARDWARE=1 uv run pytest -m hardware \
    packages/brother_printer/tests/hardware/test_print.py {{ args }}
  ```

- **`test-all`** — the entire suite including hardware tests:

  ```
  BROTHER_PRINTER_HARDWARE=1 uv run pytest {{ args }}
  ```

This pairs naturally with the negative-path tests planned here: since the new `TapeMismatchError` / `ImageScalingError` cases consume zero tape, they could even fit under a `test-connect`-style non-destructive grouping if we tag them accordingly. Worth deciding whether to separate by file path (as above) or introduce a finer-grained marker (e.g. `hardware_destructive`) so `test-connect` stays robust as tests move between files.

Add a `### Added` (or `### Changed`) CHANGELOG entry for the new recipes when implemented.

---

# [Comment #3]() by [c-vigo]()

_Posted on June 4, 2026 at 01:08 PM_

## Additional scope: scoped `just` hardware test recipes

Add three recipes to `justfile.project` (alongside existing `test-hardware`):

| Recipe | What it runs | Tape |
|--------|----------------|------|
| `just test-connect` | `test_connectivity.py` + `test_status.py` | None (discover, open/close, status round-trip, CLI status) |
| `just test-print` | `test_print.py` only | Consumes tape (P0–P4 print matrix) |
| `just test-all` | Full `pytest` with `BROTHER_PRINTER_HARDWARE=1` | Includes hardware print tests |

All three set `BROTHER_PRINTER_HARDWARE=1`; `test-connect` and `test-print` narrow paths instead of `-m hardware` on the whole tree.

**Also update:** `TESTING.md` run-command table and `CHANGELOG.md` `### Added` (developer workflow).

**Suggested acceptance criteria additions:**

- [ ] `just test-connect`, `just test-print`, and `just test-all` recipes in `justfile.project`
- [ ] `TESTING.md` documents when to use each recipe
- [ ] `CHANGELOG.md` entry for the new recipes

