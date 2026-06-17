# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0](https://github.com/exoma-ch/brother-printer/releases/tag/0.2.0) - 2026-06-17

### Added

- **`brother-ptouch-label --replicate N` (alias `--repeat`) for cable-wrap "flag" labels** ([#45](https://github.com/exoma-ch/brother-printer/issues/45))
  - Repeats the text `N` times along the axis perpendicular to its reading direction, so a single label stays legible when wrapped around a cable (useful with flexible-ID TZe-FX tapes)
  - Without `--rotate`, copies stack across the printable height and each is auto-fitted to `print_height / N`; with `--rotate`, copies repeat along the feed axis at full width
  - Accepts `--replicate auto` to fit as many copies as the tape and font size allow (needs `--font-size`, plus `--width` when combined with `--rotate`)
  - Respects the self-laminating white band: replicated copies stack within the confined print height
  - Defaults to `1` (no replication), so existing renders are unchanged
- **Confine printing to the white band on self-laminating tape** ([#41](https://github.com/exoma-ch/brother-printer/issues/41))
  - When the printer reports self-laminating media (`MediaType.SELF_LAMINATING` `0x16` or `TapeColor.WHITE_SELF_LAMINATING` `0x80`), printing is automatically limited to the narrow printable white strip and anchored at the white-strip edge, instead of spanning the full tape width onto the clear laminate flap
  - `brother-ptouch-driver info tapes` now reports the self-laminating printable band per width alongside the per-width print areas
  - Applies to every print path — direct PNG (`brother-ptouch-driver print`), rendered text (`brother-ptouch-label`), and chained strips/CSV — via a shared effective-print-height in the imaging pipeline; text is rendered directly at the band height so it stays crisp rather than downscaled
  - Auto-detected from live printer status (no new flag); the clear-flap region is left unprinted, and direct PNG printing follows the existing fit rule (band-height image, or `--scale` to resize) so QR sharpness is preserved
  - New helpers `effective_print_pins`, `is_self_laminating`, and `self_laminating_band_pins` in `brother_ptouch_driver.protocol.enums`

### Changed

- **Package versions are now derived from the git release tag** (hatch-vcs) instead of hardcoded strings
  - Both `brother-ptouch-driver` and `brother-ptouch-label` declare `dynamic = ["version"]`; the version reported by `--version` (and `brother_ptouch_driver.__version__`) is computed from the most recent `X.Y.Z` tag, so the release tag is the single source of truth and `--version` no longer drifts from the actual release
  - Off-tag builds report a development version (e.g. `0.2.1.devN+g<sha>`); a clean `X.Y.Z` is reported only at the exact tag

### Fixed

- **Self-laminating printable band is per-tape-width, not a fixed height** ([#50](https://github.com/exoma-ch/brother-printer/issues/50))
  - The white-strip band added in #41 assumed a single fixed ~9.8 mm (140 px) height for every tape width; hardware testing on a PT-E920BT showed the strip scales with tape width, so on wider tape (e.g. 36 mm TZe-SL261) content was confined to far less than the actual ~15 mm strip
  - Replace the single `SELF_LAMINATING_BAND_PINS` constant with a per-`TapeWidth` band table looked up by `effective_print_pins()` — 24 mm → 120 px (8.5 mm), 36 mm → 156 px (11 mm), both hardware-measured; `self_laminating_band_pins()` now takes the tape width
  - `brother-ptouch-driver info tapes` shows the measured band per width instead of one fixed `self-laminating` row
- **`just` recipes dropped quoting on space-containing arguments** ([#42](https://github.com/exoma-ch/brother-printer/issues/42))
  - `just label "Flex ID"` expanded `{{ args }}` as raw text, so the shell word-split the label into two CLI arguments (`Got unexpected extra argument`)
  - Enable `set positional-arguments` and forward `"$@"` instead of `{{ args }}` in the `discover`, `printer-status`, `tapes`, `print`, `label` and `setup-usb` recipes so quoted arguments survive intact
- **`status` crash on "no tape" and unrecognised media/colour bytes** ([#39](https://github.com/exoma-ch/brother-printer/issues/39))
  - Add `TapeColor.NO_TAPE` (`0x00`) and the documented extended-palette colours, plus `MediaType.SELF_LAMINATING` (`0x16`, field-reported on self-laminating 24/36 mm tape)
  - Decode undocumented media/colour bytes to the raw value (rendered as `unknown (0xNN)`) instead of raising, so querying status never crashes; `NO_TAPE` renders as `No tape`
  - Add `TapeColor.WHITE_SELF_LAMINATING` (`0x80`, field-reported on white self-laminating tape such as TZe-SL251; the plain laminated TZe-S251 reports `WHITE` on the same printer)
  - Render colours whose name repeats the cartridge type (heat-shrink, self-laminating, flexible ID — e.g. `WHITE_FLEX_ID`/TZe-FX251) as just the colour (`White`), since the cartridge type already appears on the Media line
- **`setup-usb.sh` crash on `curl | bash` install** ([#37](https://github.com/exoma-ch/brother-printer/issues/37))
  - Guard `${BASH_SOURCE[0]}` with a `$0` default so the documented piped install no longer prints `BASH_SOURCE[0]: unbound variable` under `set -u`
  - Apply the same hardening to the vendor and devcontainer helper scripts

## [0.1.0](https://github.com/exoma-ch/brother-printer/releases/tag/0.1.0) - 2026-06-08

### Added

- **Open-source PT-E920BT driver and CLI** ([#2](https://github.com/exoma-ch/brother-printer/issues/2), [#3](https://github.com/exoma-ch/brother-printer/issues/3))
  - Python implementation of the P-touch raster protocol from scratch; build-strategy and architecture ADRs under `docs/adr/`
  - Two-package uv workspace: `brother-ptouch-driver` (`import brother_ptouch_driver`) and `brother-ptouch-label` (`import brother_ptouch_label`)
  - Console scripts: `brother-ptouch-driver`, `brother-ptouch-label`
  - Five-layer architecture (transport, protocol, imaging, library API, CLI) documented in ADR-0002; driver/text decoupling in ADR-0003

- **USB transport and printer discovery** ([#4](https://github.com/exoma-ch/brother-printer/issues/4))
  - `Transport` protocol, `UsbTransport` via pyusb, and `discover()` for PT-E920BT (`04f9:224b`)
  - `brother-ptouch-driver discover` CLI subcommand with optional `--status`
  - Kernel driver detach on open; chunked bulk OUT writes for large jobs
  - udev sample rules and Linux USB setup guide under `docs/install/linux-usb.md`
  - Devcontainer USB passthrough and opt-in `just test-hardware` pytest marker

- **P-touch raster protocol encoder and status decoder** ([#5](https://github.com/exoma-ch/brother-printer/issues/5))
  - Pure-function encoder for raster commands and `encode_job()` single-page jobs
  - `encode_strip_job()` multi-page encoder with chained feed and cut control
  - 32-byte status reply decoder with TZe tape-width mapping and human-readable errors
  - Golden-file tests under `tests/protocol/golden/`

- **Image-to-raster pipeline** ([#6](https://github.com/exoma-ch/brother-printer/issues/6))
  - `image_to_raster()` converts PIL images to 70-byte raster lines centered on the print head
  - Strict threshold conversion (no dithering) and integer nearest-neighbor scaling via `--scale`
  - Image height must match tape print area unless `scale=True`; `TapeWidth.print_area_left_pins` for head positioning
  - `ImagingError` and `ImageScalingError` re-exported from the library API

- **Image print CLI and library orchestration** ([#7](https://github.com/exoma-ch/brother-printer/issues/7))
  - `brother-ptouch-driver print PATH --tape {3.5|6|9|12|18|24|36}mm` with `--auto-cut`/`--no-cut`, `--copies`, `--threshold`, and `--scale`
  - `print_image()`, `print_png()`, and `print_strip()` library APIs with tape-width safety check against printer status
  - Opt-in hardware print-matrix tests with per-width label fixtures; regenerate via `just gen-fixtures-driver`

- **Status, discover --status, and info tapes** ([#8](https://github.com/exoma-ch/brother-printer/issues/8), [#19](https://github.com/exoma-ch/brother-printer/issues/19))
  - `brother-ptouch-driver status [-p ID]` shows loaded tape, color, media type, phase, and error state
  - `brother-ptouch-driver discover -s/--status` queries each printer with graceful per-device failure handling
  - `brother-ptouch-driver info tapes` lists supported TZe widths and printable pixel widths at 360 dpi
  - Library API: `query_status()`, `select_printer()`, and `PrinterStatus` re-export

- **Half-cut label strips and daisy-chained multi-label printing** ([#21](https://github.com/exoma-ch/brother-printer/issues/21))
  - `print_strip()` library API; CLI accepts multiple paths or `--csv FILE` for chained strips
  - `--half-cut`/`--no-half-cut` and `--strip`/`--no-strip`; CSV schema with `image` and optional `copies` columns
  - `HalfCutNotSupportedError` when `half_cut=True` on non-laminated loaded tape
  - Opt-in hardware test prints a two-label half-cut strip (laminated tape only)

- **Text label rendering and printing** ([#3](https://github.com/exoma-ch/brother-printer/issues/3), [#25](https://github.com/exoma-ch/brother-printer/issues/25))
  - `brother-ptouch-label` CLI and `brother_ptouch_label` library: `render_text`, `max_font_size`, `print_text`, `detect_tape_width`
  - Multi-line labels with auto-fit font size (capped at 48px), alignment, line spacing, and 90° rotation across the tape
  - Per-edge margins, fixed label width (`--width`), optional `--tape` with auto-detect from printer status
  - `--output` / `-o` writes a PNG without printing

- **Vendor documentation and reference material** ([#1](https://github.com/exoma-ch/brother-printer/issues/1))
  - Provenance index, fetch/convert scripts, User's Guide and raster text dumps under `docs/vendor/`
  - USB ID and TZe tape width tables; half-cut compatibility notes

- **Test infrastructure and hardware validation** ([#9](https://github.com/exoma-ch/brother-printer/issues/9), [#22](https://github.com/exoma-ch/brother-printer/issues/22), [#27](https://github.com/exoma-ch/brother-printer/issues/27))
  - `LoopbackTransport` for hardware-free end-to-end print golden tests
  - Consolidated hardware tests under `tests/hardware/` with shared `conftest.py` and minimal-tape print matrix
  - Label package golden-image tests with bundled DejaVuSans.ttf
  - Scoped recipes: `just test-driver`, `just test-label`, `just test-connect`, `just test-print`, `just test-all`
  - Root `TESTING.md` documents suite layout, golden files, and hardware prerequisites

- **Linux USB setup script** ([#10](https://github.com/exoma-ch/brother-printer/issues/10))
  - `packaging/scripts/setup-usb.sh` installs libusb, udev rules, and `plugdev` membership in one step
  - Runnable from a checkout or standalone via `curl`; `just setup-usb` recipe; `--devcontainer` flag for dev hosts
