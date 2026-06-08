---
type: issue
state: closed
created: 2026-05-28T15:20:37Z
updated: 2026-05-29T07:52:29Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/1
comments: 1
labels: chore, priority:high, area:docs, effort:medium
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:54.546Z
---

# [Issue 1]: [[CHORE] Collect official PT-E920BT documentation under docs/vendor/](https://github.com/exoma-ch/brother-printer/issues/1)

## Description

Collect official Brother documentation for the PT-E920BT and store it locally for reference and AI-assisted development.

## Problem Statement

Before implementing the P-touch raster protocol and CLI, we need authoritative documentation (command references, USB descriptors, tape specifications) accessible in-repo without relying on external URLs.

## Acceptance Criteria

- [ ] Gather PT-E920BT User's Guide, P-touch Template Command Reference, Raster Command Reference, and ESC/P command reference (where applicable)
- [ ] Store documents under `docs/vendor/` with provenance metadata (source URL, version, retrieval date) in `docs/vendor/INDEX.md`
- [ ] Convert PDFs to text/markdown for grep-friendly AI usage (e.g. via `pdftotext` or `marker`)
- [ ] If Brother licensing forbids redistribution, commit only extracted facts + links (not the PDFs themselves)
- [ ] Document USB vendor/product IDs and known endpoints for PT-E920BT
- [ ] Document supported TZe tape widths (3.5, 6, 9, 12, 18, 24, 36 mm) and printable pixel widths at 360 dpi

## Implementation Notes

- Target directory: `docs/vendor/`
- Index file: `docs/vendor/INDEX.md`
- Check Brother developer portal and product support pages
- Note any differences between PT-E920BT and other P-touch models documented

## Related Issues

Part of v0.1 roadmap epic (parent issue to be linked).

## Priority

High — blocks protocol implementation and ADR decisions.

---

# [Comment #1]() by [c-vigo]()

_Posted on May 28, 2026 at 03:21 PM_

Part of v0.1 roadmap epic #11

