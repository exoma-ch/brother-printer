---
type: issue
state: closed
created: 2026-05-28T15:20:51Z
updated: 2026-05-29T07:52:31Z
author: c-vigo
author_url: https://github.com/c-vigo
url: https://github.com/exoma-ch/brother-printer/issues/4
comments: 1
labels: feature, priority:high, area:transport, effort:medium, semver:minor
assignees: c-vigo
milestone: none
projects: none
parent: none
children: none
synced: 2026-06-06T05:55:53.282Z
---

# [Issue 4]: [[FEATURE] USB transport layer with discover for PT-E920BT](https://github.com/exoma-ch/brother-printer/issues/4)

## Description

Implement USB transport layer for PT-E920BT on Linux using pyusb/libusb, with printer discovery support.

## Problem Statement

v0.1 requires printing over USB from a Linux host. We need a transport abstraction that handles device detection, bulk endpoint communication, and read/write timeouts.

## Proposed Solution

- Implement `Transport` protocol/ABC in `src/brother_printer/transport/`
- USB backend via `pyusb` + `libusb1` (cross-platform library, but v0.1 targets Linux only)
- Detect PT-E920BT by vendor/product ID
- Expose `discover()` to list connected Brother P-touch printers
- Handle bulk IN/OUT endpoints with configurable timeouts

## Acceptance Criteria

- [ ] `Transport` interface: `open()`, `close()`, `write(bytes)`, `read(n) -> bytes`
- [ ] USB implementation finds PT-E920BT by VID/PID
- [ ] `brother-printer discover` CLI sub-command lists connected printers with identifier string
- [ ] Graceful error messages for: no device found, permission denied (udev hint), device busy
- [ ] Unit tests with mock/in-memory transport stub (real USB tests manual only)

## Implementation Notes

- Linux-only for v0.1; document udev rules requirement for non-root access
- Consider `/dev/usb/lp0` as future alternative; pyusb preferred for control/status reads
- Depends on #3 (package skeleton) and #2 (build-strategy ADR)

## Related Issues

- Depends on #2, #3
- Blocks #5, #7, #8
- Part of v0.1 roadmap epic

## Priority

High

---

# [Comment #1]() by [c-vigo]()

_Posted on May 28, 2026 at 03:21 PM_

Part of v0.1 roadmap epic #11

