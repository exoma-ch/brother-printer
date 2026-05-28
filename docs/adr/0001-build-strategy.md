# ADR-0001: Build strategy for PT-E920BT

## Status

Accepted — 2026-05-28

## Context

The [v0.1 roadmap](https://github.com/exoma-ch/brother-printer/issues/11)
targets a Linux USB CLI that prints arbitrary images (primarily QR code images) on a Brother
PT-E920BT with tape selection and auto-cut control. Before writing transport or protocol
code, two decisions must be locked:

1. **Protocol family** — P-touch raster vs ESC/P vs other.
2. **Build approach** — implement from scratch, fork an existing project, or wrap one as
   a subprocess dependency.

Official PT-E920BT documentation collected in issue [#1](https://github.com/exoma-ch/brother-printer/issues/1)
is indexed in [docs/vendor/INDEX.md](../vendor/INDEX.md). Canonical hardware facts live in
[usb-ids.md](../vendor/usb-ids.md) and [tze-tape-widths.md](../vendor/tze-tape-widths.md).

The PT-E920BT is a P-touch industrial printer (360 dpi, 560-pin head, TZe tapes up to
36 mm). It is **not** a QL-series printer and does not use the QL raster protocol.

## Decision

### 1. Use the P-touch raster protocol

Implement direct USB communication using Brother's P-touch **raster** command set.

Evidence:

- Brother advertises **Raster** and **Mobile SDK** as the PT-E920BT host languages; ESC/P
  and P-touch Template are not offered — see
  [escp-command-reference.md](../vendor/escp-command-reference.md) and
  [INDEX.md](../vendor/INDEX.md).
- PT-E920BT is **absent** from Brother's
  [command-reference model list](https://support.brother.com/g/s/es/dev/en/command/reference/index.html);
  the closest published raster manual is the PT-P900/P910BT family proxy already stored
  under `docs/vendor/`.
- The 560-pin / 360 dpi print head and TZe tape-width tables match the PT-P910BT family
  per [tze-tape-widths.md](../vendor/tze-tape-widths.md).

### 2. Build a from-scratch Python implementation

Write a new Python library and CLI in this repository. Treat all prior-art projects as
**reference implementations** — study their protocol handling, transport patterns, and
user-pain themes — but do not fork them or depend on them at runtime.

Rationale:

- The repository is already a Python project (`pyproject.toml`, `src/brother_printer/`).
- No existing project supports PT-E920BT; wrapping would still require full protocol work
  plus an external binary dependency.
- The closest match (`ptouch-print`) is C and GPL-3.0; forking would split the ecosystem
  across languages and copyleft boundaries.
- `brother_ql` is architecturally excellent but implements the **incompatible** QL raster
  protocol.

## Consequences

### Positive

- Unblocks [#4](https://github.com/exoma-ch/brother-printer/issues/4) (USB transport),
  [#5](https://github.com/exoma-ch/brother-printer/issues/5) (raster encoder), and
  [#6](https://github.com/exoma-ch/brother-printer/issues/6) (image pipeline) with a
  single coherent protocol target.
- Keeps licensing simple (project is Apache-2.0) and avoids GPL copyleft from
  `brother_ql` / `ptouch-print`.
- Allows tailoring the imaging pipeline for QR sharpness at 360 dpi — a recurring pain
  point across prior art.

### Negative / constraints

- Full raster encoder and status decoder must be implemented and validated on hardware;
  the PT-P900-family manual is a **proxy**, not a PT-E920BT-specific spec.
- v0.1 is locked to USB raster only; Bluetooth, ESC/P, or Mobile SDK would require a
  new ADR.
- Prior-art bug fixes (e.g. 360 dpi support in `ptouch-print`) cannot be consumed
  automatically — they must be re-evaluated and ported.

## Prior-art comparison

Survey date: **2026-05-28**. GitHub metadata and open-issue samples collected via `gh api`;
project pages fetched directly.

| Project | Language | Protocol | License | Activity | PT-E920BT |
| --- | --- | --- | --- | --- | --- |
| [ptouch-print](https://git.familie-radermacher.ch/linux/ptouch-print.git/) | C | P-touch raster | GPL-3.0 | Active (360 dpi work Mar 2026; maintainer ~1–2 h/month) | **No** — supports PT-E500, PT-D460BT, etc.; 360 dpi marked untested |
| [brother_ql](https://github.com/pklaus/brother_ql) | Python | QL raster | GPL-3.0 | Active (691★, 84 open issues) | **No** — QL-series only |
| [brother_ql_web](https://github.com/pklaus/brother_ql_web) | Python | QL raster (via brother_ql) | GPL-3.0 | Moderate (315★; last push Aug 2023) | **No** — open issues request P-touch support ([#57](https://github.com/pklaus/brother_ql_web/issues/57)) |
| [brother-label](https://github.com/nametacker/brother-label) | Python | P-touch raster | MIT | Archived (2018) | **No** |
| [python-brotherprint](https://github.com/fozzle/python-brotherprint) | Python | ESC/P + Template | MIT | Unmaintained (2020; seeking maintainer) | **No** — QL-580N / QL-720NW network |
| [brother_escp](https://github.com/butterware/brother_escp) | Ruby | ESC/P | MIT | Stale (2016) | **No** — TD-4000 tested |
| [pt1230](https://github.com/cbdevnet/pt1230) | C | P-touch raster (180 dpi) | None declared | Stale (2018) | **No** — PT-1230PC (64 px / 180 dpi) |
| [pklaus related-software gist](https://gist.github.com/pklaus/aeb55e18d36690df6a84a3eab49e9fd7) | — | Index of QL ecosystem + misc | — | Curated list | **No** PT-E920BT entry |

### Recurring user-pain themes (from open issues)

| Theme | Where seen | Relevance to v0.1 |
| --- | --- | --- |
| Barcode / QR quality and pixel-precise sizing | `brother_ql` README emphasises per-pixel control; threshold/dither options | Directly motivates [#6](https://github.com/exoma-ch/brother-printer/issues/6) |
| Tape / label size selection | `brother_ql` — wrong label type, 62 mm tape failures ([#148](https://github.com/pklaus/brother_ql/issues/148)); `brother_ql_web` — PT-series requests | Maps to CLI `--tape` and media-width bytes in [tze-tape-widths.md](../vendor/tze-tape-widths.md) |
| Auto-cut / cut-after-last-label | `brother_ql` ([#150](https://github.com/pklaus/brother_ql/issues/150)); `pt1230` ([#14](https://github.com/cbdevnet/pt1230/issues/14), cut-before-label) | Maps to [#7](https://github.com/exoma-ch/brother-printer/issues/7) |
| Model support gaps | All surveyed projects; `ptouch-print` page lists PT-E500 but not PT-E920BT | Confirms greenfield PT-E920BT work is required |
| USB discovery / permissions | `brother_ql` discovery failures; `ptouch-print` udev rules | Informs [#4](https://github.com/exoma-ch/brother-printer/issues/4) |
| DPI / resolution mismatches | `ptouch-print` — 360 dpi support added but untested; project page still warns >180 dpi | PT-E920BT is 360 dpi; cannot rely on upstream without validation |

## PT-E920BT support status

| Source | PT-E920BT listed? | Closest model / notes |
| --- | --- | --- |
| Brother command-reference page | **No** | PT-P910BT (360 dpi raster manual available) |
| Prior-art code search (`PT-E920`, `E920BT`) | **No matches** in all 8 projects | — |
| [docs/vendor/INDEX.md](../vendor/INDEX.md) | Documented via User's Guide + P900-family raster proxy | 560-pin / 360 dpi head shared with PT-P910BT |
| `ptouch-print --list-supported` | **No** (PT-E500 supported; E920 absent) | PT-E500 needs blank-line workarounds per upstream docs |

**Conclusion:** PT-E920BT support must be built in this repository. The PT-P910BT raster
command reference (proxy) is the best published protocol baseline; hardware validation in
[#5](https://github.com/exoma-ch/brother-printer/issues/5) remains mandatory.

## Alternatives considered

### Fork `ptouch-print`

**Rejected.** Closest functional match (P-touch raster, libusb, CLI, auto tape detection),
but C + GPL-3.0 conflicts with the Python/Apache-2.0 direction of this repo. PT-E920BT is
not in the supported-model list; 360 dpi support was added recently and is explicitly
**untested**. Maintainer bandwidth is very limited (~1–2 hours per month).

### Wrap `ptouch-print` as a subprocess

**Rejected.** Would still require PT-E920BT to be supported upstream first, adds a
compile-time C dependency and GPL boundary at the integration point, and prevents fine-
grained control over the 360 dpi imaging pipeline needed for QR quality.

### Extend / fork `brother_ql`

**Rejected.** QL and P-touch raster protocols are different despite both being called
"Brother raster". Different command sequences, media definitions, and supported models.
`brother_ql_web` open issues confirm P-touch is a separate effort. GPL-3.0 applies.

### Use ESC/P via `brother_escp` or `python-brotherprint`

**Rejected.** PT-E920BT does not advertise ESC/P ([escp-command-reference.md](../vendor/escp-command-reference.md)).
Existing ESC/P libraries target QL network printers or TD-series label printers, not
360 dpi P-touch industrial models.

### Use `pt1230` or `brother-label` as a base

**Rejected.** Both target legacy 180 dpi / narrow-head models (64 px for PT-1230PC).
Protocol and line-payload sizes differ from the 560-pin / 70-byte PT-E920BT raster format.
Projects are stale or archived.

### Depend on Brother Mobile SDK

**Rejected for v0.1.** Proprietary, platform-specific, and unsuitable for a headless Linux
CLI. Out of scope per roadmap [#11](https://github.com/exoma-ch/brother-printer/issues/11).

## What to borrow from prior art (without forking)

| Pattern | Source | Apply in |
| --- | --- | --- |
| Transport backends (pyusb, discover) | `brother_ql` | [#4](https://github.com/exoma-ch/brother-printer/issues/4) |
| Raster command sequencing and status decode | `ptouch-print`, `pt1230`, vendor manual | [#5](https://github.com/exoma-ch/brother-printer/issues/5) |
| Threshold / no-dither for barcodes | `brother_ql` `--threshold` | [#6](https://github.com/exoma-ch/brother-printer/issues/6) |
| udev permission rules | `ptouch-print` `udev/` directory | [#4](https://github.com/exoma-ch/brother-printer/issues/4) |

## References

### Prior art (issue #2 survey list)

- [ptouch-print](https://git.familie-radermacher.ch/linux/ptouch-print.git/) — [project page](https://dominic.familie-radermacher.ch/projekte/ptouch-print/)
- [brother_ql](https://github.com/pklaus/brother_ql)
- [brother_ql related software (gist)](https://gist.github.com/pklaus/aeb55e18d36690df6a84a3eab49e9fd7)
- [brother_ql_web](https://github.com/pklaus/brother_ql_web)
- [brother-label](https://github.com/nametacker/brother-label)
- [python-brotherprint](https://github.com/fozzle/python-brotherprint)
- [brother_escp](https://github.com/butterware/brother_escp)
- [pt1230](https://github.com/cbdevnet/pt1230)

### Canonical vendor documentation (this repo)

- [docs/vendor/INDEX.md](../vendor/INDEX.md)
- [docs/vendor/usb-ids.md](../vendor/usb-ids.md)
- [docs/vendor/tze-tape-widths.md](../vendor/tze-tape-widths.md)
- [docs/vendor/ptouch-raster-command-reference.md](../vendor/ptouch-raster-command-reference.md)
- [docs/vendor/escp-command-reference.md](../vendor/escp-command-reference.md)

### Project issues

- [#2](https://github.com/exoma-ch/brother-printer/issues/2) — this ADR
- [#11](https://github.com/exoma-ch/brother-printer/issues/11) — v0.1 roadmap
