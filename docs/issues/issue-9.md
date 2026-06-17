---
type: issue
state: closed
created: 2026-05-28T15:21:04Z
updated: 2026-06-04T15:35:25Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/9
comments: 3
labels: chore, priority:medium, area:testing, effort:medium
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:51.242Z
---

# [Issue 9]: [[CHORE] Loopback transport and golden-file test harness](https://github.com/exoma-ch/brother-printer/issues/9)

## Description

Build a loopback/in-memory transport and golden-file test suite for protocol and imaging layers, enabling CI without hardware.

## Problem Statement

CI has no PT-E920BT hardware. We need deterministic tests for protocol encoding, status decoding, and image rasterization.

## Proposed Solution

- `LoopbackTransport`: in-memory transport that records writes and returns canned status replies
- Golden files: known input image → expected raster bytes; known command sequence → expected byte stream
- pytest fixtures for transport and protocol round-trips

## Acceptance Criteria

- [ ] `LoopbackTransport` implements `Transport` interface from #4
- [ ] Golden-file tests for protocol encoder output (at least one minimal print job)
- [ ] Golden-file tests for status decoder (parse known 32-byte replies)
- [ ] Golden-file tests for imaging pipeline (QR-like pattern → raster lines)
- [ ] All tests run in CI without hardware (`just test` / pytest)
- [ ] Document how to add new golden files when protocol changes

## Implementation Notes

- Target: `tests/` with `tests/fixtures/golden/` for byte snapshots
- Pattern reusable for v0.2 web service integration tests
- Can start early alongside #5 and #6; finalize before release

## Related Issues

- Depends on #3; integrates with #4, #5, #6
- Part of v0.1 roadmap epic

## Priority

Medium

---

# [Comment #1]() by [c-vigo]()

_Posted on May 28, 2026 at 03:21 PM_

Part of v0.1 roadmap epic #11

---

# [Comment #2]() by [c-vigo]()

_Posted on June 3, 2026 at 12:42 PM_

## Re-assessment against current `dev`

Most of this chore has effectively landed (likely via #4/#6). Status per acceptance criterion:

| Criterion | Status | Evidence |
| --- | --- | --- |
| `LoopbackTransport` implements `Transport` | ❌ Not done | No `LoopbackTransport` exists. Closest is the private `_TransportStub` in `tests/transport/test_transport_protocol.py` — records writes / echoes reads, but test-local, not reusable, and does **not** return canned status replies. |
| Golden-file tests for encoder output (≥1 minimal job) | ✅ Done | `test_encode_job_matches_golden` / `test_encode_strip_job_matches_golden` in `tests/protocol/test_encoder.py` vs `tests/protocol/golden/minimal_job_24mm.bin` (+ 3-page strip golden). |
| Golden-file tests for status decoder (32-byte replies) | ✅ Done | `test_decode_status_golden` in `tests/protocol/test_decoder.py` vs `status_ready_24mm.bin` (32 bytes). |
| Golden-file tests for imaging pipeline (QR-like → raster) | 🟡 Partial | `tests/imaging/test_raster.py` covers a QR-like checkerboard → raster lines, but via computed assertions rather than byte-snapshot golden files. |
| All tests run in CI without hardware | ✅ Done | `.github/workflows/ci.yml` runs `just test`; hardware tests gated behind the `hardware` marker + `BROTHER_PRINTER_HARDWARE` skipif (never set in CI). |
| Document how to add new golden files when protocol changes | ❌ Not done | `TESTING.md` references golden files but documents no regeneration/add procedure (unlike `just gen-test-images` for PNG fixtures). |

### Remaining work
1. A reusable `LoopbackTransport` that returns canned status replies (the explicit first criterion).
2. Optional: literal golden snapshots for the imaging pipeline (currently covered by computed assertions).
3. Docs for adding/regenerating protocol golden files.

Suggest re-scoping this issue down to items 1–3 rather than closing outright.

---

# [Comment #3]() by [c-vigo]()

_Posted on June 4, 2026 at 03:35 PM_

Implemented in #30 (merged into dev): LoopbackTransport + widened Transport protocol (read_exact), real end-to-end print_image golden through the loopback, golden-file regeneration documented in TESTING.md, and imaging errors re-exported from the library API with the ADR-0002 import guard extended to imaging.

