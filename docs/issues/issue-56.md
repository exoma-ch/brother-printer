---
type: issue
state: closed
created: 2026-06-18T12:25:31Z
updated: 2026-10-06T08:50:50Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/56
comments: 1
labels: feature, area:protocol, area:cli, effort:medium, semver:minor
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-10-06T09:36:16.374Z
---

# [Issue 56]: [[FEATURE] Chunked strip printing: half-cut within chunks, full cut between](https://github.com/exoma-ch/brother-printer/issues/56)

## Description

Add support for printing a strip of many images where labels within a chunk are separated by **half-cuts**, and chunks are separated by **full cuts**. For example: print 10 PNGs with half-cuts between them, a full cut, 10 more with half-cuts, a full cut, and so on.

## Problem Statement

Today `print_strip()` treats half-cut and full auto-cut as mutually exclusive. In [`encode_strip_job`](packages/brother_ptouch_driver/src/brother_ptouch_driver/protocol/encoder.py#L184):

```python
effective_auto_cut = auto_cut and not half_cut
```

So a strip job is either:
- `half_cut=True` → half-cut between *every* page, and `CMD_CUT_EACH` is omitted entirely (no full cuts anywhere), or
- `auto_cut=True, half_cut=False` → full cut every N pages via `cut_each(...)`.

There's a `cut_each_n` parameter in `encode_strip_job` that could give "full cut every N pages", but (a) it's not wired through `print_strip()` (defaults to cut-per-page), and (b) it only fires when `effective_auto_cut` is true, i.e. `half_cut` must be off. So "half-cut between labels" **and** "full cut every N" cannot be combined.

Use case: batch-printing large numbers of labels (e.g. peelable labels on laminated tape) where you want the labels within a group held together by half-cuts for easy handling, but each group of N physically separated by a full cut.

## Proposed Solution

Introduce a **per-page cut type** ("half" / "full" / "none") in the encoder, plus a convenience that derives the pattern from a chunk size:

1. In `encode_strip_job`, decide the cut per page rather than via a single global flag. The strip loop already emits a fresh `set_mode(...)` + `advanced_mode(half_cut=...)` block per page ([encoder.py:187-206](packages/brother_ptouch_driver/src/brother_ptouch_driver/protocol/encoder.py#L187-L206)), so the machinery is mostly in place.
2. For page `i`: emit a **full cut** when `(i+1) % chunk_size == 0` or it's the last page; otherwise emit a **half cut**.
3. Expose `chunk_size: int | None` on `print_strip()` and a `--cut-every N` flag on the `print` CLI command.

## Alternatives Considered

- **Separate job per chunk**: doesn't work cleanly — a `half_cut=True` job ejects its last page under half-cut mode, so chunk boundaries come out as half-cuts, not full cuts.
- Exposing `cut_each_n` alone: insufficient, since it's gated behind `auto_cut` and can't coexist with half-cut.

## Additional Context

Caveat to validate on real hardware before relying on this: whether the PT-E920BT honors a mid-job switch between half-cut and full-cut advanced-mode blocks within one chained job. If not, the fallback is one job per chunk with a forced full cut at each chunk's final eject. Recommend landing the encoder change with unit tests (extending the existing half-cut strip coverage in `test_encoder.py`) to verify the byte stream before hardware testing.

## Impact

- Benefits anyone batch-printing many labels who wants grouped, separable output.
- Backward compatible: new optional `chunk_size` / `--cut-every` parameter; existing behavior unchanged when not set.

---

# [Comment #1]() by [c-vigo]()

_Posted on October 6, 2026 at 08:50 AM_

Done in #65 (merged to `dev` as `b5a49d1`). `print_strip(chunk_size=N)` and `brother-ptouch-driver print --cut-every N`: labels inside a chunk joined by half-cuts, a full cut between chunks. Default behavior is unchanged, byte for byte.

## Correction to "Alternatives Considered"

The per-page encoding this issue proposed is the right byte stream but does **not** work on the PT-E920BT. **The printer applies the cut settings of a job's first page to every page of that job.** Measured on 6 mm white laminated TZe:

| Job sent | Expected | Actual |
| --- | --- | --- |
| 5 pages, full-cut blocks on pages 2, 4, 5 (page 1 half-cut) | 3 pieces of tape | **1 continuous strip, 4 half-cuts** |
| 5 pages, uniform full-cut blocks on every page | 5 separate labels | 5 separate labels |
| 2 jobs × 2 pages, each half-cut then full-cut at its end | 2 pieces, half-cut inside each | 2 pieces, half-cut inside each |

Row 2 shows per-page cutting itself works (`ESC i M 40` + `ESC i A 01` cuts between pages); only switching the cut *kind* mid-job is ignored.

So the rejected alternative is what shipped — **one job per chunk** — because the premise for rejecting it was wrong: a half-cut job's final eject does **not** stay a half-cut. Every job ends in a full cut, which is exactly what puts the boundary where a chunk ends. Full-cut-only chunking needs no split and goes through `ESC i A`'s cut-each-N counter in a single job, which finally makes the long-dead `cut_each_n` parameter reachable.

The encoder's per-page `chunk_size` resolver still does the work; it now runs per chunk job rather than across the whole strip. Cost of the split is the head-to-cutter feed at each boundary — inherent to making a full cut there.

Recorded in `_strip_jobs()`'s docstring, the `CHANGELOG.md` entry, and `TESTING.md`'s H3 note (new opt-in hardware case H3, which prints the five-label/chunk-of-two strip and documents what each wrong outcome means).

**Not verified on hardware:** `--cut-every N` without `--half-cut` for N > 1. It rests on `ESC i A`'s documented behavior plus the N=1 measurement above.


