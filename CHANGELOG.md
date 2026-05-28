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

### Changed

### Deprecated

### Removed

### Fixed

### Security
