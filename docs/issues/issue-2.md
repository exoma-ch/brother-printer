---
type: issue
state: closed
created: 2026-05-28T15:20:42Z
updated: 2026-05-29T07:52:30Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/2
comments: 1
labels: chore, priority:high, area:docs, effort:medium
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:54.119Z
---

# [Issue 2]: [[CHORE] Prior-art deep-dive and build-strategy ADR for PT-E920BT](https://github.com/exoma-ch/brother-printer/issues/2)

## Description

Investigate existing open-source solutions for Brother label printing, evaluate user feedback, and produce a build-strategy ADR for this project.

## Problem Statement

PT-E920BT is a P-touch industrial printer (360 dpi, TZe tapes), not a QL-series printer. We need to understand which prior-art projects are protocol-compatible, what users report as pain points, and whether to build from scratch, fork, or wrap existing code.

## Acceptance Criteria

- [ ] Review and compare: [ptouch-print](https://git.familie-radermacher.ch/linux/ptouch-print.git/), [brother_ql](https://github.com/pklaus/brother_ql), [brother_ql related software list](https://gist.github.com/pklaus/aeb55e18d36690df6a84a3eab49e9fd7), [brother_ql_web](https://github.com/pklaus/brother_ql_web), [nametacker/brother-label](https://github.com/nametacker/brother-label), [python-brotherprint](https://github.com/fozzle/python-brotherprint), [brother_escp](https://github.com/butterware/brother_escp), [pt1230](https://github.com/cbdevnet/pt1230)
- [ ] Survey open issues and user feedback in the most relevant repos (barcode/QR quality, tape selection, auto-cut, model support gaps)
- [ ] Identify whether PT-E920BT is already supported in any project; if not, note closest model and protocol differences
- [ ] Recommend: raster vs ESC/P, from-scratch vs fork vs wrap
- [ ] Publish ADR at `docs/adr/0001-build-strategy.md` with decision, rationale, and rejected alternatives

## Implementation Notes

- QL-series tools (brother_ql) are architecturally inspirational but protocol-incompatible
- ptouch-print is the closest C implementation; recently adding 360 dpi support
- ADR should unblock protocol (#5) and transport (#4) implementation choices
- Depends on documentation collection (#1) for cross-checking command references

## Related Issues

- Depends on #1
- Blocks protocol and transport implementation issues
- Part of v0.1 roadmap epic

## Priority

High — de-risks the protocol layer before coding begins.

---

# [Comment #1]() by [c-vigo]()

_Posted on May 28, 2026 at 03:21 PM_

Part of v0.1 roadmap epic #11

