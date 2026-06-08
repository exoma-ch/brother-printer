# Testing

How to run the test suite, what it covers, and how hardware tests use tape.

## Running tests

| Command | What it does |
| --- | --- |
| `just test` | Full pytest suite; hardware tests are **skipped** (no env var). |
| `just test-cov` | Same with coverage report (`term-missing`). |
| `just test-hardware [args]` | Sets `BROTHER_PTOUCH_DRIVER_HARDWARE=1` and runs `pytest -m hardware`. |
| `just test-connect [args]` | Non-destructive hardware checks (`test_connectivity.py` + `test_status.py`); requires the printer but consumes no tape. |
| `just test-print [args]` | Tape-consuming print matrix (`test_print.py` only). |
| `just test-all [args]` | Full pytest suite with hardware tests enabled. |
| `just gen-fixtures-driver` | Regenerates committed PNG fixtures under `packages/brother_ptouch_driver/tests/hardware/assets/`. |

Hardware tests are gated by the `hardware` marker (registered in `pyproject.toml`) and
`pytest.mark.skipif` when `BROTHER_PTOUCH_DRIVER_HARDWARE` is not set to `1`. They are
skipped during CI and a normal `just test` unless you opt in with
`BROTHER_PTOUCH_DRIVER_HARDWARE=1`.

**Hardware prerequisites:** PT-E920BT connected over USB, passthrough into the
devcontainer, udev permissions — see [docs/install/linux-usb.md](docs/install/linux-usb.md).

Before the first print run, regenerate fixtures if needed: `just gen-fixtures-driver`
(all `label_*.png` files must exist under `packages/brother_ptouch_driver/tests/hardware/assets/`).

**Timeouts:** print tests poll status with 15s per attempt and tolerate no-reply while
the printer is busy. Idle wait allows up to **3 minutes** after chained print jobs.

## Software suite layout

| Directory | Coverage |
| --- | --- |
| `packages/brother_ptouch_driver/tests/protocol/` | Encoder/decoder golden files, constants, enums |
| `packages/brother_ptouch_driver/tests/transport/` | USB transport (pyusb mocked), `LoopbackTransport`, discover, errors |
| `packages/brother_ptouch_driver/tests/imaging/` | `image_to_raster` pipeline (strict sizing, `--scale`) |
| `packages/brother_ptouch_driver/tests/` | Driver library orchestration (`print_image`, `print_png`, `print_strip`, `query_status`) and the `LoopbackTransport` end-to-end golden |
| `packages/brother_ptouch_driver/tests/cli/` | Driver CLI commands, CSV jobs, import boundaries (ADR-0002) |
| `packages/brother_ptouch_label/tests/` | Text rendering (`render_text`, `max_font_size`, `print_text`, `brother-ptouch-label` CLI) |

## Golden files

Deterministic byte/image snapshots committed under the suite. They run in CI
with no hardware:

| Golden | Source of truth |
| --- | --- |
| `tests/protocol/golden/*.bin` | Encoder/decoder output for fixed inputs |
| `tests/golden/print_image_24mm.bin` | Full status-request + encoded job captured through `LoopbackTransport` for a 24 mm checkerboard |
| `packages/brother_ptouch_label/tests/assets/golden/*.png` | `render_text` output |

`LoopbackTransport` (`brother_ptouch_driver.transport.LoopbackTransport`) is the
hardware-free, in-memory transport used to capture these bytes: it records every
`write()` and replays canned `read`/`read_exact` replies, so `print_image` runs
the real imaging and encoder path with no USB device.

**Regenerating after an intentional protocol or imaging change:** the
end-to-end golden is rewritten in place when `UPDATE_GOLDEN` is set:

```bash
UPDATE_GOLDEN=1 just test    # rewrites tests/golden/print_image_24mm.bin
```

Review the resulting diff carefully and commit it only when the byte change is
expected. Encoder/decoder `.bin` goldens are committed snapshots; update them the
same way you would any fixture when the documented protocol output changes.

## Hardware suite layout

All opt-in hardware tests live under `packages/brother_ptouch_driver/tests/hardware/`:

| File | Role |
| --- | --- |
| `conftest.py` | Shared markers, fixtures (`printer`, `loaded_tape`, `label_fixture_path`, …), status helpers |
| `test_connectivity.py` | `discover()` and USB open/close |
| `test_status.py` | Status round-trip, `query_status`, CLI `status` and `discover --status` |
| `test_print.py` | Minimal-tape print matrix (H1–H2) |

Fixtures: `packages/brother_ptouch_driver/tests/hardware/assets/` — per-width `label_*.png` files;
regenerate with `just gen-fixtures-driver`.

## Hardware print matrix

Each full `just test-hardware` run on **one loaded tape** exercises the matrix below.
Hardware prints verify only **physical actions** (marking, chained feed, cutter); imaging
options (`threshold`, `scale`, text layout, copies, `print_png`, raw `encode_job`) are
covered by software golden/imaging tests without tape.

### Non-printing tests (0 labels)

| Test | What it verifies |
| --- | --- |
| `test_connectivity.py::test_discover_finds_connected_printer` | USB discovery, PT-E920BT identity |
| `test_connectivity.py::test_open_close_round_trip` | Interface claim/release |
| `test_status.py::test_status_request_round_trip` | Raw `status_request()` 32-byte reply |
| `test_status.py::test_query_status_library_api` | `query_status()` library path |
| `test_status.py::test_status_cli_command` | `brother-ptouch-driver status` |
| `test_status.py::test_discover_status_cli_flag` | `brother-ptouch-driver discover --status` |
| `test_print.py::test_print_wrong_width_raises_tape_mismatch` | `TapeMismatchError` when requested width ≠ loaded tape (zero tape) |
| `test_print.py::test_print_wrong_height_raises_scaling_error` | `ImageScalingError` when height ≠ print area and `scale=False` (zero tape) |

### Printing tests

| ID | Test | Labels / strip | Features exercised |
| --- | --- | --- | --- |
| **H1** | `test_print_chained_strip` | 1 auto-cut strip (2 pages, **one cut** at end) | `print_strip`, chained multi-page feed (`print_page`/FF between pages, `eject` at end), auto-cut cutter |
| **H2** | `test_print_half_cut_strip` | 1 half-cut strip (2 pages) | `print_strip`, `half_cut=True`, chained multi-page, auto-cut forced off; **laminated tape only** |

**Rough total per run:** one short 2-page auto-cut strip (H1) plus one short half-cut strip
(H2) when laminated tape is loaded; otherwise H1 only.

**Head-to-cutter clearance:** the ~24 mm blank tape before the first printed segment
(and the feed before each cut) is inherent to the PT-E920BT mechanics, not test-layout waste.

### Fixture assets

| Asset | Purpose |
| --- | --- |
| `label_{width}mm.png` | Text-only label stating image height in mm and px plus rendered font size (e.g. `H = 12 mm` / `H = 150 px` / `FS = 48`); height = `TapeWidth.print_area_pins`, width = minimum needed for the text; strict 1-bit |

Pin counts per width: [docs/vendor/tze-tape-widths.md](docs/vendor/tze-tape-widths.md).

## Per-tape behavior

- Hardware print tests use **only the loaded tape**: `status.media_width` is read at
  runtime; tests skip if no tape is reported.
- The matching `label_*` fixture is selected from the loaded width; missing files skip
  with a message to run `just gen-fixtures-driver`.
- `print_image` / `print_strip` call `_validate_status`; a width mismatch raises
  `TapeMismatchError`.
- Half-cut (H2) requires **laminated** TZe/HGe; non-laminated tape skips H2.
- To cover another width, swap tape and re-run `just test-hardware`.

## Coverage gaps (hardware)

Not exercised on a physical printer today:

| Gap | Notes |
| --- | --- |
| `print_text` | `brother_ptouch_label.print_text` and `render_text` covered by software tests only |
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

When adding features, follow the TDD workflow described in
[CONTRIBUTING.md](CONTRIBUTING.md).
