---
type: issue
state: closed
created: 2026-06-02T19:14:24Z
updated: 2026-06-03T12:38:26Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/22
comments: 0
labels: docs, refactor, priority:low, area:testing
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:48.768Z
---

# [Issue 22]: [[DOCS] Add TESTING.md and homogenize the hardware-test layout](https://github.com/exoma-ch/brother-printer/issues/22)

## Summary
Two related test-hygiene items:
1. There is no browsable doc of what the test suite covers or what `just test-hardware` physically prints (only test docstrings + the fixture generator). Add a root `TESTING.md`.
2. Hardware tests are split across two conventions — co-located `*_hardware*` files and the `tests/hardware/` folder — with duplicated helpers. Consolidate into one approach.

## Part A — Add `TESTING.md`
New root `TESTING.md` with:
- How to run: `just test` / `just test-cov` (hardware auto-skipped via `skipif`), `just test-hardware [args]` (`-m hardware`), `just gen-test-images`; `hardware` marker registered in `pyproject.toml`.
- Software suite layout: `tests/protocol/` (constants, encoder/decoder golden, enums), `tests/transport/` (discover, USB transport, protocol, errors — pyusb mocked), `tests/imaging/` (`image_to_raster` pipeline), `tests/` + `tests/cli/` (`print_image`/`print_strip` orchestration and CLI).
- Hardware print matrix — what each test prints (6 labels/run, single loaded tape):
  - `test_hardware.py` — `discover()` + USB open/close. No print.
  - `test_hardware_status.py` — `status_request()` 32-byte round-trip → `REPLY`. No print.
  - `test_hardware_print.py::test_print_label` — `encode_job(..., no_chain=True)`, 60 solid-black lines (~4 mm), default auto-cut. 1 label.
  - `test_print_matrix.py::test_print_matrix[0|90]` — `print_image()` of the tape-matched QR fixture at rotate 0 and 90, default `auto_cut=True`. 2 labels.
  - `test_print_strip.py::test_print_half_cut_strip` — `print_strip()` of 3 copies, `half_cut=True` (chained `encode_strip_job`). 3-label strip.
  - Features exercised: `print_image`, `print_strip`, rotation 0/90, auto-cut, half-cut, chained multi-page, raw `encode_job`, discovery, status decode.
- Tape dependence: each run tests only the loaded tape (read `status.media_width`, skip if absent, pick fixture from `_TAPE_FIXTURES`, `_validate_status()` raises `TapeMismatchError` on mismatch). Fixtures are sized per width to `TapeWidth.print_area_pins` (48-454, see `docs/vendor/tze-tape-widths.md`); each is a square QR with a top orientation bar that makes rotation visible. Cover more widths by swapping tape and re-running.
- Coverage gaps (untested on hardware): `copies>1`, `threshold`, `margin`, `allow_distortion`, `mirror`, `auto_cut=False`.
- Future plans: link v0.1 roadmap #11, hardware validation of tape-width tables (#5), hardware-test items #4/#7, v0.2 web service.
- TDD pointer: `.cursor/rules/tdd.mdc`.
- Add a "Testing" link from `README.md` to `TESTING.md`.

## Part B — Homogenize hardware tests
All hardware tests share the `@pytest.mark.hardware` + `skipif(BROTHER_PRINTER_HARDWARE)` gate, but live under two conventions and duplicate helpers.

Proposed single approach: move every hardware test under `tests/hardware/` and extract shared logic into `tests/hardware/conftest.py`.
- Move + rename:
  - `tests/transport/test_hardware.py` → `tests/hardware/test_connectivity.py`
  - `tests/protocol/test_hardware_status.py` → `tests/hardware/test_status.py`
  - `tests/protocol/test_hardware_print.py` → `tests/hardware/test_print_basic.py`
- New `tests/hardware/conftest.py` holds `_read_status`, `_wait_for_printer_idle`, `_query_loaded_tape`, `_TAPE_FIXTURES`, and the `printer` / `loaded_tape` / `fixture_path` fixtures (currently duplicated in `test_print_strip.py` and `test_print_matrix.py`). Optionally centralize the `pytestmark` (marker + skipif).

## Out of scope / invariants
- No change to what is printed or to test assertions.
- `just test-hardware` must collect the exact same set of tests (the `hardware` marker is the single source of truth).
- Software tests must keep passing unchanged; no new lint warnings.

## Acceptance criteria
- [ ] `TESTING.md` exists at repo root and is linked from `README.md`.
- [ ] `TESTING.md` documents the hardware print matrix, per-tape behavior, coverage gaps, and future plans.
- [ ] All hardware tests live under `tests/hardware/` with shared helpers in `tests/hardware/conftest.py` (no duplication).
- [ ] `uv run pytest` and `BROTHER_PRINTER_HARDWARE=1 uv run pytest -m hardware --co` collect the same tests as before.

## Changelog
Added (TESTING.md); Changed (test layout).

