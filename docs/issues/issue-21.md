---
type: issue
state: closed
created: 2026-06-02T16:48:59Z
updated: 2026-06-03T09:21:32Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/21
comments: 1
labels: feature, area:protocol, area:cli
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:49.144Z
---

# [Issue 21]: [[FEATURE] Half-cut labels and daisy-chained label strips](https://github.com/exoma-ch/brother-printer/issues/21)

## Description

Add support for half-cut (peelable) labels and daisy-chained multi-label strips. Users should be able to print a strip of labels with half-cuts between them and a single full cut at the end, from multiple image paths on the command line or from a CSV file.

## Problem Statement

Earlier hardware tests showed auto-cut not working as expected for multiple copies. Root cause: `print_image()` builds one single-page job and re-sends the whole byte stream N times. Each copy is an independent job (`ESC @` ... `Control-Z`) so the printer fully cuts after every copy and there is no way to chain labels into a strip.

The PT-E920BT has a dual full/half cutter built for peel-and-apply half-cut strips. The protocol already exposes the needed flags (`ESC i M` auto-cut, `ESC i A` cut-each-N, `ESC i K` half-cut/no-chain); we just don't assemble multi-page jobs or send `ESC i A`.

## Proposed Solution

1. Add `ESC i A` ("cut each N labels") encoder command.
2. Add `encode_strip_job()` multi-page encoder; refactor `encode_job()` to delegate.
3. Add `print_strip()` orchestration (status once, rasterize each image, one write).
4. Extend CLI `print` command: multiple paths, `--csv`, `--half-cut`, `--strip`.
5. CSV schema v1: `image` (required), `copies` (optional int).

Target cut behavior for a strip: `auto_cut=on`, `cut_each_n = number_of_labels`, `no_chain=on`, `half_cut=on` — half-cuts between labels, single full cut at the end.

## Alternatives Considered

- **Per-label half-cut via page-grouping**: images joined on one page, page boundary = half-cut. Deferred — half-cut is job-global in v1.
- **Separate `print-strip` subcommand**: rejected in favor of extending existing `print` command.
- **Separate bugfix issue for auto-cut on copies**: folded into this feature since multi-page refactor fixes it.

## Impact

- Users can batch-print peelable label strips (common PT-E920BT use case).
- `--copies N` on a single image keeps current separate-job behavior unless `--strip` is passed (backward compatible).
- Half-cut is job-global in v1 (matches printer's marketed batch mode).

## Changelog Category

Added

## Acceptance criteria

- [ ] `cut_each()` encoder for ESC i A with golden bytes
- [ ] `encode_strip_job()` multi-page encoder with golden bytes
- [ ] `print_strip()` library API
- [ ] CLI: multi-path, `--csv`, `--half-cut`, `--strip`
- [ ] Opt-in hardware test for half-cut strip
- [ ] TDD compliance (see .cursor/rules/tdd.mdc)
---

# [Comment #1]() by [c-vigo]()

_Posted on June 2, 2026 at 04:49 PM_

## Implementation plan

### Why (problem)

Earlier hardware tests showed auto-cut "not working as expected" for multiple copies. Root cause: `print_image()` builds **one single-page job** and re-sends the whole byte stream N times (`printing.py:105-108`). Each copy is an independent job (`ESC @` ... `Control-Z`) so the printer fully cuts after every copy and there is no way to chain labels into a strip.

The PT-E920BT has a dual full/half cutter built for "peel-and-apply half-cut strips". The protocol already exposes the needed flags; we just don't assemble multi-page jobs or send `ESC i A`.

### Protocol facts

- Mode commands are **job-global**, sent once in the header: `ESC i M` auto-cut (bit 6), `ESC i A` "cut each N labels" (n=1..255; **n=0 = never cut**), `ESC i K` half-cut (bit 2) + no-chain (bit 3).
- Only raster data + the page terminator repeat per page: `FF` (0x0C) ends a non-last page, `Control-Z` (0x1A) ends the last page.
- `ESC i A` (`1B 69 41`) is **not implemented** today.
- Half-cut is on/off **for the whole job**, not per individual label.

Target cut behavior for a strip: `auto_cut=on`, `cut_each_n = number_of_labels`, `no_chain=on`, `half_cut=on`.

### Implementation (TDD)

1. Protocol constant + encoder for `ESC i A`
2. Multi-page job encoder (`encode_strip_job()`); refactor `encode_job()` to delegate
3. Library orchestration (`print_strip()`)
4. CLI: multi-path, `--csv`, `--half-cut`, `--strip`
5. CHANGELOG + docs
6. Opt-in hardware test

### Tests

- Unit: `cut_each()`, `encode_strip_job()` golden bytes, single-page golden unchanged
- Unit: `print_strip()` orchestration
- CLI: multi-path, CSV, flag wiring
- Hardware (opt-in): 2-3 label half-cut strip

