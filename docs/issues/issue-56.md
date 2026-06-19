---
type: issue
state: open
created: 2026-06-18T12:25:31Z
updated: 2026-06-19T06:49:38Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/56
comments: 0
labels: feature, area:protocol, area:cli, effort:medium, semver:minor
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-19T07:07:55.120Z
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

