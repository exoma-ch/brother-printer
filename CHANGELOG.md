# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- **Driver and text decoupling (uv workspace)** ([#3](https://github.com/exoma-ch/brother-printer/issues/3))
  - `brother_printer_text` workspace package with `render_text`, `max_font_size`, and `print_text`
  - `brother-label-text` CLI for text labels (`--font`, `--font-size`, `--align`, `--line-spacing`)
  - `print_png(bytes)` entrypoint on the core library for PNG-at-the-edge callers
  - ADR-0003 documents the split, strict image-height contract, and `--scale` behavior

- **Direct text printing** ([#25](https://github.com/exoma-ch/brother-printer/issues/25))
  - Multi-line labels with auto-fit font size (50px minimum), alignment, spacing, and baked-in rotation
  - Text rotation renders full-length labels along the tape (90° matches 0°, 270° matches 180°) so long text is never cropped
  - Hardware print matrix P4 for text labels; requires `pillow>=10.1` for scalable default font

- **Text package rendering and CLI enhancements**
  - Real 0°/90° rotation (`--rotate` flag); 180°/270° removed
  - Per-edge margins (`--margin-top`, `--margin-bottom`, `--margin-left`, `--margin-right`) and `--width` fixed label width
  - `brother-label-text` positional text argument; optional `--tape` with auto-detect from printer status
  - `--output` / `-o` writes a PNG without printing; `detect_tape_width()` exported from `brother_printer_text`

- **Text package golden-image tests and per-package test recipes** ([#9](https://github.com/exoma-ch/brother-printer/issues/9))
  - Bundled DejaVuSans.ttf and committed PNG goldens for deterministic `render_text` regression tests
  - `just test-core`, `just test-text`, and `just gen-text-images` for scoped test runs and fixture regeneration

### Changed

- **brother-label-text CLI and rotation behavior**
  - Text is a positional argument (`--text` removed); `--tape` optional (auto-detect from printer status)
  - `--rotate` toggles 90° across-tape layout; 180°/270° rotation removed
  - Per-edge margin options and `--width` for fixed label length; `-o` renders PNG without printing

- **Symmetric uv workspace layout** ([#3](https://github.com/exoma-ch/brother-printer/issues/3))
  - Core package and tests moved to `packages/brother_printer/`; repo root is a virtual workspace root
  - Both workspace members now live under `packages/`; see ADR-0003

- **Strict image height for printing** ([#3](https://github.com/exoma-ch/brother-printer/issues/3))
  - `print_image` / `image_to_raster` require image height to match tape print area unless `scale=True` or `--scale`
  - `scale=True` uses lossless integer nearest-neighbor when possible; non-integer factors resample
  - Renamed `allow_distortion` to `scale` across library and CLI

### Removed

- **Text printing from core package** ([#3](https://github.com/exoma-ch/brother-printer/issues/3))
  - `render_text`, `max_font_size`, and `print_text` no longer exported from `brother_printer`
  - `brother-printer print --text` removed; use `brother-label-text` instead

- **TESTING.md and consolidated hardware print matrix** ([#22](https://github.com/exoma-ch/brother-printer/issues/22))
  - Root `TESTING.md` documents run commands, suite layout, per-tape behavior, coverage gaps, and the P0–P3 hardware print matrix
  - All hardware tests under `tests/hardware/` with shared `conftest.py`; grayscale and distort fixtures via `just gen-test-images`
  - Minimal-tape matrix: P1 sends one `encode_strip_job` chained strip (FF between pages, single end cut) for rotations/threshold/distortion; plus raw encode, half-cut strip, and full-cut copies

- **PT-E920BT vendor documentation** ([#1](https://github.com/exoma-ch/brother-printer/issues/1))
  - Provenance index, fetch/convert scripts, User's Guide and raster text dumps, USB ID and TZe tape width tables under `docs/vendor/`

- **Build-strategy ADR for PT-E920BT** ([#2](https://github.com/exoma-ch/brother-printer/issues/2))
  - Decision to implement P-touch raster from scratch in Python; prior-art comparison and rejected alternatives recorded in `docs/adr/0001-build-strategy.md`

- **Architecture ADR and package skeleton** ([#3](https://github.com/exoma-ch/brother-printer/issues/3))
  - ADR-0002 documents the 5-layer architecture (transport, protocol, imaging, library API, CLI) and v0.2 web-service reuse path
  - Empty `transport/`, `protocol/`, `imaging/`, `cli/` subpackages with responsibility docstrings

- **Downstream `promote-release.yml` workflow** ([#463](https://github.com/vig-os/devcontainer/issues/463))
  - Template at `.github/workflows/promote-release.yml`: validate draft release and release PR, publish release, merge to `main`, best-effort git RC tag cleanup

- **USB transport layer with discover** ([#4](https://github.com/exoma-ch/brother-printer/issues/4))
  - `Transport` protocol, `UsbTransport` via pyusb, and `discover()` for PT-E920BT
  - `brother-printer discover` CLI subcommand (Click)
  - udev sample rule and Linux USB setup guide under `docs/install/linux-usb.md`
  - Devcontainer USB passthrough (`/dev/bus/usb`) and libusb backend for hardware verification
  - Opt-in `just test-hardware` pytest marker for connected PT-E920BT smoke tests
  - Devcontainer udev rule (`99-brother-ptouch_devcontainer.rules`) for rootless Podman USB permissions
  - Project venv console scripts on PATH inside devcontainer
  - PT-E920BT USB product ID confirmed as 0x224B on live hardware
  - `just discover` recipe for USB printer enumeration

- **P-touch raster protocol encoder and status decoder** ([#5](https://github.com/exoma-ch/brother-printer/issues/5))
  - Pure-function encoder for raster commands and `encode_job()` minimal single-page jobs
  - 32-byte status reply decoder with TZe tape-width mapping and human-readable error messages
  - Golden-file tests under `tests/protocol/golden/`
  - Opt-in hardware print smoke test (`just test-hardware`) validates `encode_job()` on a connected PT-E920BT

- **Image-to-raster pipeline tuned for QR code quality** ([#6](https://github.com/exoma-ch/brother-printer/issues/6))
  - `image_to_raster()` converts PIL images to 70-byte raster lines centered on the print head
  - Strict threshold conversion (no dithering), integer nearest-neighbor scaling, rotation, and margin support
  - Rejects non-integer scale factors that would distort QR modules; `TapeWidth.print_area_left_pins` for head positioning
  - Unit tests with synthetic checkerboard patterns under `tests/imaging/`

- **CLI print command with tape selection and auto-cut** ([#7](https://github.com/exoma-ch/brother-printer/issues/7))
  - `brother-printer print PATH --tape {3.5|6|9|12|18|24|36}mm` with `--auto-cut`/`--no-cut`, `--copies`, `--threshold`, `--rotate`, `--margin`, and `--printer`
  - `print_image()` library orchestrator with tape-width safety check against printer status
  - Opt-in hardware print-matrix test with pre-computed QR fixtures under `tests/hardware/assets/`; regenerate via `just gen-test-images`

- **CLI status, discover --status, and info tapes** ([#8](https://github.com/exoma-ch/brother-printer/issues/8), [#19](https://github.com/exoma-ch/brother-printer/issues/19))
  - `brother-printer status [-p ID]` shows loaded tape, color, media type, phase, and error state
  - `brother-printer discover -s/--status` queries each printer with graceful per-device failure handling
  - `brother-printer info tapes` lists supported TZe widths and printable pixel widths at 360 dpi
  - Library API: `query_status()`, `select_printer()`, and `PrinterStatus` re-export; CLI routes through `brother_printer` only ([#18](https://github.com/exoma-ch/brother-printer/issues/18))

- **Half-cut label strips and daisy-chained multi-label printing** ([#21](https://github.com/exoma-ch/brother-printer/issues/21))
  - `encode_strip_job()` multi-page encoder with `ESC i A` cut-each-N support; `print_strip()` library API
  - `brother-printer print` accepts multiple paths or `--csv FILE` for chained strips; `--half-cut`/`--no-half-cut` and `--strip`/`--no-strip`
  - CSV schema: required `image` column and optional `copies` column (paths relative to the CSV file)
  - Opt-in hardware test prints a two-label half-cut strip (laminated tape only)
  - `HalfCutNotSupportedError` when `half_cut=True` on non-laminated loaded tape; see `docs/vendor/tze-tape-widths.md`

### Changed

- **Hardware test layout homogenized** ([#22](https://github.com/exoma-ch/brother-printer/issues/22))
  - Connectivity, status, and print tests consolidated under `tests/hardware/`; removed scattered `*_hardware*` modules in `tests/protocol/` and `tests/transport/`
  - P1 visual-variations strip uses one chained job instead of repeated `print_image` ejects (eliminates blank tape between segments); hardware margin case dropped

- **Hardware QR fixtures show rotation on printed labels** ([#7](https://github.com/exoma-ch/brother-printer/issues/7))
  - Square fixtures with a top-edge orientation bar so `rotate=90` is visible on hardware; regenerate via `just gen-test-images`
  - Unit tests prove rotation changes raster bytes and that four quarter-turns restore the image
  - Print-matrix hardware test waits until the printer is idle and uses longer status timeouts; matrix trimmed to two rotation cases (auto-cut removed because single-page jobs always feed and cut when no-chain is enabled)

### Deprecated

### Removed

### Fixed

- **UsbTransport.write sends full large jobs** ([#22](https://github.com/exoma-ch/brother-printer/issues/22))
  - Bulk OUT writes loop in 16 KiB chunks until all bytes are sent; fixes truncated multi-page strips when the printer throttles USB intake

- **Half-cut label strips and centered QR on tape** ([#21](https://github.com/exoma-ch/brother-printer/issues/21))
  - Multi-page half-cut strips emit a per-page control block (ESC i z before ESC i K), disable auto-cut, and omit cut-each
  - Raster packing uses the right-margin head offset per Brother §2.3.5 so images are centered on the tape

- **Single-page encode_job() feed and auto-cut on hardware** ([#5](https://github.com/exoma-ch/brother-printer/issues/5))
  - Default to no-chain mode so labels feed out and auto-cut after the last page
  - Hardware print smoke test uses 60 raster lines (above the 57-dot TZe minimum)

- **USB transport open on kernel-bound devices** ([#4](https://github.com/exoma-ch/brother-printer/issues/4))
  - Detach kernel driver before set_configuration; use pyusb util helpers for claim/release

- **Devcontainer rebuild on rootless Podman** ([#4](https://github.com/exoma-ch/brother-printer/issues/4))
  - Removed `device_cgroup_rules` and `group_add: keep-groups` from shared compose overrides; rootless Podman rejects cgroup device rules and does not implement Docker's keep-groups

### Security
