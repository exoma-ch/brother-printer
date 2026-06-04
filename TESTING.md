# Testing

How to run the test suite, what it covers, and how hardware tests use tape.

## Running tests

| Command | What it does |
| --- | --- |
| `just test` | Full pytest suite; hardware tests are **skipped** (no env var). |
| `just test-cov` | Same with coverage report (`term-missing`). |
| `just test-hardware [args]` | Sets `BROTHER_PRINTER_HARDWARE=1` and runs `pytest -m hardware`. |
| `just gen-test-images` | Regenerates committed PNG fixtures under `packages/brother_printer/tests/hardware/assets/`. |

Hardware tests are gated by the `hardware` marker (registered in `pyproject.toml`) and
`pytest.mark.skipif` on `BROTHER_PRINTER_HARDWARE=1`. They never run during CI or a
normal `just test` unless you opt in.

**Hardware prerequisites:** PT-E920BT connected over USB, passthrough into the
devcontainer, udev permissions — see [docs/install/linux-usb.md](docs/install/linux-usb.md).

Before the first print run, regenerate fixtures if needed: `just gen-test-images`
(all `qr_*`, `gray_*`, and `distort_100.png` must exist under `packages/brother_printer/tests/hardware/assets/`).

**Timeouts:** print tests poll status with 15s per attempt and tolerate no-reply while
the printer is busy. Idle wait allows up to **3 minutes** after long strips (P1).

## Software suite layout

| Directory | Coverage |
| --- | --- |
| `packages/brother_printer/tests/protocol/` | Encoder/decoder golden files, constants, enums |
| `packages/brother_printer/tests/transport/` | USB transport (pyusb mocked), discover, errors |
| `packages/brother_printer/tests/imaging/` | `image_to_raster` pipeline (strict sizing, `--scale`) |
| `packages/brother_printer/tests/` | Core library orchestration (`print_image`, `print_png`, `print_strip`, `query_status`) |
| `packages/brother_printer/tests/cli/` | Core CLI commands, CSV jobs, import boundaries (ADR-0002) |
| `packages/brother_printer_text/tests/` | Text rendering (`render_text`, `max_font_size`, `print_text`, `brother-label-text` CLI) |

## Hardware suite layout

All opt-in hardware tests live under `packages/brother_printer/tests/hardware/`:

| File | Role |
| --- | --- |
| `conftest.py` | Shared markers, fixtures (`printer`, `loaded_tape`, `fixture_path`, …), status helpers |
| `test_connectivity.py` | `discover()` and USB open/close |
| `test_status.py` | Status round-trip, `query_status`, CLI `status` and `discover --status` |
| `test_print.py` | Minimal-tape print matrix (P0–P4) |

Fixtures: `packages/brother_printer/tests/hardware/assets/` — QR, grayscale gradient, and `distort_100.png`;
regenerate with `just gen-test-images`.

## Hardware print matrix

Each full `just test-hardware` run on **one loaded tape** exercises the matrix below.
Approximate tape use is listed per test; P1 packs many option checks onto one continuous
strip with a single cut at the end (`cut_each` after the last page; no cuts between pages).

### Non-printing tests (0 labels)

| Test | What it verifies |
| --- | --- |
| `test_connectivity.py::test_discover_finds_connected_printer` | USB discovery, PT-E920BT identity |
| `test_connectivity.py::test_open_close_round_trip` | Interface claim/release |
| `test_status.py::test_status_request_round_trip` | Raw `status_request()` 32-byte reply |
| `test_status.py::test_query_status_library_api` | `query_status()` library path |
| `test_status.py::test_status_cli_command` | `brother-printer status` |
| `test_status.py::test_discover_status_cli_flag` | `brother-printer discover --status` |

### Printing tests

| ID | Test | Labels / strip | Features exercised |
| --- | --- | --- | --- |
| **P0** | `test_print_raw_label` | ~1 short full-cut label | Raw `encode_job()`, `no_chain=True`, solid-black raster, default auto-cut |
| **P1** | `test_print_visual_variations_strip` | 1 continuous strip, **one cut** at end | `image_to_raster` per variation + single `encode_strip_job(..., auto_cut=True)` (FF between pages, `cut_each` on last page); `rotate` 0/90/180/270, `threshold` (grayscale fixture), `scale=True` (distort fixture); no per-page eject feed |
| **P2** | `test_print_half_cut_strip` | 1 half-cut strip (2 pages) | `print_strip`, `half_cut=True`, chained multi-page, auto-cut forced off; **laminated tape only** |
| **P3** | `test_print_full_cut_strip_copies` | 2 full-cut labels | `print_strip(copies=2)`, `cut_each`, FF page chaining, full multi-page auto-cut |
| **P4** | `test_print_text_feature_matrix` | 1 continuous strip, **one cut** at end | `render_text` + `print_strip`: auto-fit default font, multi-line + `align`, fixed `font_size`, `rotate=90` |

**Rough total per run:** ~4–5 cut labels plus one half-cut strip (P2), while covering
rotations, threshold, `scale`, and chained multi-page encoding without blank
tape between P1 segments.

**Head-to-cutter clearance:** the ~24 mm blank tape before the first printed segment on P1
(and the feed before each cut) is inherent to the PT-E920BT mechanics, not per-segment
waste from the test layout.

### Fixture assets

| Asset | Purpose |
| --- | --- |
| `qr_{width}mm.png` | Square QR + top orientation bar; side = `TapeWidth.print_area_pins` |
| `gray_{width}mm.png` | Vertical grayscale gradient for `threshold` |
| `distort_100.png` | 100×100 px; non-integer scale to every tape width for `scale=True` |

Pin counts per width: [docs/vendor/tze-tape-widths.md](docs/vendor/tze-tape-widths.md).

## Per-tape behavior

- Hardware print tests use **only the loaded tape**: `status.media_width` is read at
  runtime; tests skip if no tape is reported.
- The matching `qr_*` / `gray_*` fixture is selected from the loaded width; missing
  files skip with a message to run `just gen-test-images`.
- `print_image` / `print_strip` call `_validate_status`; a width mismatch raises
  `TapeMismatchError`.
- Half-cut (P2) requires **laminated** TZe/HGe; non-laminated tape skips P2.
- To cover another width, swap tape and re-run `just test-hardware`.

## Coverage gaps (hardware)

Not exercised on a physical printer today:

| Gap | Notes |
| --- | --- |
| `print_image` / `print_image(copies>1)` | P1 uses `image_to_raster` + `encode_strip_job` directly; separate full jobs per copy not exercised on hardware |
| `print_text` | P4 uses `brother_printer_text.render_text` + `print_strip`; `brother_printer_text.print_text` covered by software tests only |
| `margin` | `apply_margin` covered by imaging unit tests only (padding breaks integer scale on tape-sized fixtures) |
| `mirror` | Encoder supports it; not exposed on `print_image` / `print_strip` |
| `no_chain=False` | Chained mode only via raw `encode_strip_job` |
| `margin_dots`, `compression`, `cut_each_n` | Encoder-only parameters |

Software tests cover imaging, encoder golden files, and mocked orchestration for most of
these paths.

## Future plans

- [Roadmap v0.1 #11](https://github.com/exoma-ch/brother-printer/issues/11)
- Hardware validation of tape-width tables [#5](https://github.com/exoma-ch/brother-printer/issues/5)
- Hardware test infrastructure [#4](https://github.com/exoma-ch/brother-printer/issues/4), fixture generator [#7](https://github.com/exoma-ch/brother-printer/issues/7)
- v0.2 web service (see [ADR-0002](docs/adr/0002-architecture.md), [ADR-0003](docs/adr/0003-driver-text-decoupling.md))

## TDD

When adding features, follow [.cursor/rules/tdd.mdc](.cursor/rules/tdd.mdc): failing test
first, minimal implementation, refactor.
