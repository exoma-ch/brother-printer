---
type: issue
state: open
created: 2026-06-16T15:41:44Z
updated: 2026-06-16T15:41:44Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/39
comments: 0
labels: bug, priority:high, area:protocol, area:cli
assignees: none
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-17T07:12:06.479Z
---

# [Issue 39]: [[BUG] status crashes on "no tape" and unrecognised media/colour bytes (self-laminating 0x16, tape colour 0x00)](https://github.com/exoma-ch/brother-printer/issues/39)

## Description

`brother-ptouch-driver status` crashes with an unhandled `ValueError` whenever the printer reports a media type or tape colour that is not in our enums. Two cases hit in real use:

1. **No tape loaded** — the status reply carries tape-colour byte `0x00`, which `TapeColor` does not define, so decoding aborts:

   ```
   ValueError: 0 is not a valid TapeColor
   ...
   ValueError: unknown tape color byte: 0x00
   ```

2. **Self-laminating tape (24 mm / 36 mm)** — the printer reports media-type byte `0x16`, which `MediaType` does not define:

   ```
   ValueError: 22 is not a valid MediaType
   ...
   ValueError: unknown media type byte: 0x16
   ```

This is especially bad for the *no tape* case: querying status is exactly how a user expects to learn that no/unknown media is loaded, yet that is the one situation that makes the command blow up.

There is an inconsistency in the decoder: `TapeWidth.from_byte` already degrades gracefully (`0x00` / unknown → `None`, see [enums.py:35-43](packages/brother_ptouch_driver/src/brother_ptouch_driver/protocol/enums.py#L35-L43)), but `media_type`, `tape_color`, `status_type`, `phase_type` and `notification` all go through `_enum_from_byte`, which re-raises on any unknown byte ([decoder.py:88-93](packages/brother_ptouch_driver/src/brother_ptouch_driver/protocol/decoder.py#L88-L93)).

## Steps to Reproduce

1. Eject the tape cassette (or load a self-laminating 24/36 mm tape).
2. Run `just printer-status` (`uv run brother-ptouch-driver status`).
3. Observe the traceback instead of a status readout.

## Expected Behavior

- `status` reports "no tape" cleanly when no cassette is loaded.
- `status` recognises self-laminating tape (24 mm and 36 mm) and flexible ID tape.
- An unknown/undocumented media or colour byte degrades gracefully (shown as e.g. `unknown (0x16)`) instead of crashing the whole command.

## Actual Behavior

The command exits non-zero with a Python traceback; no status is shown.

## Environment

- **OS**: Linux (devcontainer)
- **Image Version/Tag**: dev branch
- **Printer**: P-touch (USB)

## Additional Context

Vendor reference values:

- **Media type** table (4), [ptouch-raster-command-reference.md:1323](docs/vendor/ptouch-raster-command-reference.md#L1323). `MediaType` currently models `00/01/03/04/11/13/14/15/17/FF`. Self-laminating (`0x16`) is **not** in Brother's published P900 table but is reported by hardware in the field — it should be added. Note: flexible ID tape (`0x14`) is already mapped, so 24 mm flexible ID should already decode; worth confirming.
- **Tape colour** table (8), [ptouch-raster-command-reference.md:1443](docs/vendor/ptouch-raster-command-reference.md#L1443). `TapeColor` currently models only `01–08` + `FF` and is missing the documented `00` (no tape), `09`, `20–24`, `30/31`, `40/41`, `50–52`, `60–62`, `70`, `90/91`, `F0/F1`.

## Possible Solution

1. Add `NO_TAPE = 0x00` (and ideally the remaining documented colours) to `TapeColor`.
2. Add `SELF_LAMINATING = 0x16` to `MediaType`.
3. Make `_enum_from_byte` resilient for the *display* path: fall back to an "unknown (0xNN)" representation rather than raising, so a future undocumented byte never breaks `status`. Keep the raw byte available for diagnostics. (Alternatively, give each enum a `from_byte` classmethod mirroring `TapeWidth`.)
4. Add decoder unit tests covering `0x00` tape colour and `0x16` media type.

