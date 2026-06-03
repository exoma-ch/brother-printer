# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

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

- **Half-cut label strips and daisy-chained multi-label printing** ([#21](https://github.com/exoma-ch/brother-printer/issues/21))
  - `encode_strip_job()` multi-page encoder with `ESC i A` cut-each-N support; `print_strip()` library API
  - `brother-printer print` accepts multiple paths or `--csv FILE` for chained strips; `--half-cut`/`--no-half-cut` and `--strip`/`--no-strip`
  - CSV schema: required `image` column and optional `copies` column (paths relative to the CSV file)
  - Opt-in hardware test prints a three-label half-cut strip

### Changed

- **Hardware QR fixtures show rotation on printed labels** ([#7](https://github.com/exoma-ch/brother-printer/issues/7))
  - Square fixtures with a top-edge orientation bar so `rotate=90` is visible on hardware; regenerate via `just gen-test-images`
  - Unit tests prove rotation changes raster bytes and that four quarter-turns restore the image
  - Print-matrix hardware test waits until the printer is idle and uses longer status timeouts; matrix trimmed to two rotation cases (auto-cut removed because single-page jobs always feed and cut when no-chain is enabled)

### Deprecated

### Removed

### Fixed

- **Half-cut label strips and centered QR on tape** ([#21](https://github.com/exoma-ch/brother-printer/issues/21))
  - Raster packing uses the right-margin head offset per Brother §2.3.5 so images are centered on the tape

- **Single-page encode_job() feed and auto-cut on hardware** ([#5](https://github.com/exoma-ch/brother-printer/issues/5))
  - Default to no-chain mode so labels feed out and auto-cut after the last page
  - Hardware print smoke test uses 60 raster lines (above the 57-dot TZe minimum)

- **USB transport open on kernel-bound devices** ([#4](https://github.com/exoma-ch/brother-printer/issues/4))
  - Detach kernel driver before set_configuration; use pyusb util helpers for claim/release

### Security
