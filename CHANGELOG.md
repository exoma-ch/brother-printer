# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.3.0] - TBD

### Added

- **Chunked strip printing: half-cuts within a group, a full cut between groups** ([#56](https://github.com/exoma-ch/brother-printer/issues/56))
  - `encode_strip_job()` decided the cut once for the whole strip (`effective_auto_cut = auto_cut and not half_cut`), so a strip was either half-cut between every label with no full cut anywhere, or full-cut only. Batch-printing many peelable labels therefore had no way to keep labels grouped for handling while separating the groups physically
  - New `chunk_size` on `encode_strip_job()` resolves the cut per page: a page that closes a chunk — every `chunk_size`-th page, and the last one — takes a full cut (`ESC i M 40`, `ESC i A 01`, `ESC i K 08`), and the pages inside a chunk keep the half-cut block the strip encoder already emitted. `print_strip(chunk_size=N)` and `brother-ptouch-driver print --cut-every N` expose it; `--cut-every` implies `--strip`, so `--copies 10 --cut-every 5` chunks copies of a single image
  - **The PT-E920BT applies the cut settings of a job's first page to every page of that job.** Hardware-verified on 6 mm laminated tape: a five-page job whose pages 2, 4 and 5 carried full-cut blocks came out as one continuous strip with four half-cuts, because page 1 was half-cut. The same encoding with uniform full-cut blocks on every page (`--cut-every 1`) cut all five labels apart, so per-page cutting itself works — only switching the *kind* mid-job does not. A job's final eject full-cuts, which the issue's rejected "separate job per chunk" alternative had assumed it would not
  - `print_strip()` therefore sends a half-cut chunked strip as **one job per chunk**: each job half-cuts between its own pages and full-cuts as it ends, which the printer honours. Cost of the split is the head-to-cutter feed at every chunk boundary — inherent to a full cut, not overhead this adds. Full-cut-only chunking (`--cut-every N` without `--half-cut`) stays a single job and lets the printer's own cut-each-N counter group the pages, finally making the long-dead `cut_each_n` parameter reachable
  - `chunk_size` needs `auto_cut` (a chunk boundary *is* an auto-cut) and refuses to combine with `cut_each_n`, which drives full cuts by its own rule. Backward compatible: `chunk_size=None` reproduces both established strip streams byte for byte, pinned by an equality test against the existing encoding and by the unchanged half-cut goldens. A new golden snapshots the five-page, chunk-of-two stream
  - New opt-in hardware case **H3** (`just test-print`, laminated tape) prints a five-label strip in chunks of two; TESTING.md records the expected three pieces of tape and what each wrong outcome would mean

- **`packaging/scripts/setup-usb.sh` supports NixOS hosts, and gained a one-off grant** ([#63](https://github.com/exoma-ch/brother-printer/issues/63))
  - On NixOS every step the script performed was inapplicable: libusb dispatch found no `apt`/`dnf`/`pacman`/`zypper` and installed nothing, the udev rule copy targeted `/etc/udev/rules.d` — a read-only symlink into the Nix store — and `plugdev` neither exists nor can be created from outside the system configuration. A NixOS user following the published install docs got a warning and no working path, while the device enumerated and `open()` failed with permission denied
  - The script now detects NixOS (`/etc/NIXOS`, or `ID=nixos` in `/etc/os-release`), skips the package-manager step with a pointer to the dev shell or the user's own profile, locates the connected `04f9:224b` device through sysfs to derive its `/dev/bus/usb` node, offers to `chmod` that node after confirming, and prints the rule to declare in the system configuration rather than pretending to install it
  - The printed rule grants through `GROUP="lp"` + `MODE` and names the matching `users.users.<you>.extraGroups`, not `TAG+="uaccess"`: on NixOS the tag is applied but nothing consumes it, because the `RUN{builtin}+="uaccess"` that installs the ACL ships in systemd's `71-seat.rules` / `73-seat-late.rules`, neither of which NixOS assembles into `/etc/udev/rules.d` — so the rule goes live, `getfacl` shows no ACL, and access is still denied
  - New `--one-off` flag grants access on the currently connected printer and does nothing else — no libusb, no udev rule, no group. It needs no rebuild and is lost on replug, which is all a single hardware check wants, and it works on any distribution, not just NixOS; `--yes` skips the confirmation for unattended use. Privileged prompts decline when stdin is not a terminal instead of blocking on a prompt nobody can answer
  - [docs/install/linux-usb.md](docs/install/linux-usb.md) gains a NixOS section, and its development-shell section no longer recommends the inert `uaccess` rule. `packaging/udev/99-brother-ptouch.rules` records that `plugdev` membership is the load-bearing grant and that the `uaccess` tag adds something only where systemd's seat rules are part of the assembled rule set
  - The conventional-distribution path is unchanged and now has regression tests. Host paths come from overridable `SETUP_USB_*` variables and `main` is guarded so the script's functions can be sourced, which is what lets both paths run end to end against a fake host tree on any Linux host — including a CI runner, which is not NixOS

### Changed

- **Development environment upgraded to vigOS devkit 1.18.0 and moved to the Nix dev shell** ([#60](https://github.com/exoma-ch/brother-printer/issues/60))
  - The repo was scaffolded from devkit 0.3.4 and never upgraded, so it had drifted ~26 releases behind, across the Debian-to-Nix re-platform of the shared devcontainer image
  - `.devcontainer/` is gone; the toolchain now comes from `flake.nix` + `.envrc` (`direnv allow`, or `nix develop`). `libusb-1.0` is declared as a project package and placed on `LD_LIBRARY_PATH`, because pyusb resolves its backend through `ctypes.util.find_library` at import time. Hardware verification therefore runs against the host USB tree directly, with no device passthrough, no rootless-Podman uid remapping and no container-specific udev rule
  - This was the forcing reason for the move: the 1.18.0 image is Nix-built with no `apt`, `libusb` is not on the shared toolchain list, and container mode scaffolds no project flake in which to declare it
  - Agent skills moved from `.cursor/` to `.claude/`; the hook suite now resolves `ruff`, `typos`, `pymarkdown`, `shellcheck`, `actionlint` and `nixfmt` from the dev shell instead of pre-built wheels, and gains commit-message, branch-name and agent-identity validation
  - The release-train and `gh` helper recipes are vendored into `justfile.project`: devkit defines them only under `.devcontainer/`, which this mode does not ship. The release workflows themselves are unaffected (reported upstream as vig-os/devkit#1823)
  - The USB development-shell documentation covers NixOS hosts, where `packaging/scripts/setup-usb.sh` does not apply: it installs libusb through a distribution package manager and writes to `/etc/udev/rules.d`, which is a read-only Nix store symlink. Documents the declarative `services.udev.extraRules` equivalent, plus a one-off `chmod` for a single hardware check. The rule it first suggested used `TAG+="uaccess"`, which is inert on NixOS; corrected in [#63](https://github.com/exoma-ch/brother-printer/issues/63), which also teaches the script the NixOS path
  - Golden-image comparison is no longer byte-for-byte. Byte-exactness against a font rasterizer was only ever portable because development and CI shared one container image; the dev shell and a hosted CI runner differ by design (devkit forwards `UV_PYTHON` only on a NixOS runner), which shifts glyph advances by 1-3px and ~8px at the 48px default cap. The goldens now assert exact height (set by tape width and band confinement), width within a proportional tolerance, ink band count, and scale-normalized ink geometry — so alignment, rotation, line count, tape width and the font-size cap are all still guarded, with thresholds calibrated against the committed fixtures and pinned by tests of the comparator itself
  - Contributor-facing only — the published driver and its CLIs are unchanged. Linux USB setup for end users is unchanged; see [docs/install/linux-usb.md](docs/install/linux-usb.md) for the revised development-shell section

### Fixed

- **Renovate configuration pointed at an unsubstituted scaffold placeholder** ([#59](https://github.com/exoma-ch/brother-printer/issues/59))
  - `renovate.json` extended `github>OWNER/REPO//.github/renovate-default`, the literal template placeholder, so Renovate could not resolve the shared preset (`Cannot find preset's package`) and stopped opening dependency PRs for this repository as a precaution
  - Point it at `github>exoma-ch/brother-printer//.github/renovate-default`. The preset itself was always present at `.github/renovate-default.json`; only the reference to it was wrong

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
