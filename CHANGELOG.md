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

- **Downstream `promote-release.yml` workflow** ([#463](https://github.com/vig-os/devcontainer/issues/463))
  - Template at `.github/workflows/promote-release.yml`: validate draft release and release PR, publish release, merge to `main`, best-effort git RC tag cleanup

### Changed

### Deprecated

### Removed

### Fixed

### Security
