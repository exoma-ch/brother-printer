"""Shared fixtures and helpers for opt-in hardware tests."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from brother_ptouch_driver.protocol import (
    STATUS_REPLY_SIZE,
    decode_status,
    status_request,
)
from brother_ptouch_driver.protocol.enums import MediaType, PhaseType, TapeWidth
from brother_ptouch_driver.transport import UsbTransport, discover
from brother_ptouch_driver.transport.base import PrinterInfo
from brother_ptouch_driver.transport.errors import TransportTimeoutError

HARDWARE_ENABLED = os.environ.get("BROTHER_PTOUCH_DRIVER_HARDWARE") == "1"

PRINTER_REQUIRED_MSG = (
    "No PT-E920BT found. Confirm the printer is connected and powered, "
    "USB passthrough is configured, and udev permissions are set "
    "(see docs/install/linux-usb.md)."
)

STATUS_READ_TIMEOUT_MS = 15_000
# Chained print jobs (H1/H2) can exceed 60s on hardware; allow 3 minutes.
IDLE_WAIT_TIMEOUT_MS = 180_000
STATUS_POLL_TIMEOUT_MS = 60_000
IDLE_POLL_INTERVAL_S = 0.5

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"

_LABEL_FIXTURES: dict[TapeWidth, Path] = {
    TapeWidth.MM_3_5: _ASSETS_DIR / "label_3.5mm.png",
    TapeWidth.MM_6: _ASSETS_DIR / "label_6mm.png",
    TapeWidth.MM_9: _ASSETS_DIR / "label_9mm.png",
    TapeWidth.MM_12: _ASSETS_DIR / "label_12mm.png",
    TapeWidth.MM_18: _ASSETS_DIR / "label_18mm.png",
    TapeWidth.MM_24: _ASSETS_DIR / "label_24mm.png",
    TapeWidth.MM_36: _ASSETS_DIR / "label_36mm.png",
}

HARDWARE_PYTESTMARK = [
    pytest.mark.hardware,
    pytest.mark.skipif(
        not HARDWARE_ENABLED,
        reason="set BROTHER_PTOUCH_DRIVER_HARDWARE=1 to run hardware tests",
    ),
]


def _read_status(transport: UsbTransport):
    transport.write(status_request())
    reply = transport.read_exact(STATUS_REPLY_SIZE, timeout_ms=STATUS_READ_TIMEOUT_MS)
    return decode_status(reply)


def _ensure_status_readable(printer: PrinterInfo) -> None:
    """Poll until the printer answers status (any phase).

    Use before sending another job while the previous feed may still be active.
    Unlike idle wait, does not require EDITING phase.
    """
    deadline = time.monotonic() + STATUS_POLL_TIMEOUT_MS / 1000.0

    with UsbTransport(printer) as transport:
        while time.monotonic() < deadline:
            try:
                status = _read_status(transport)
            except TransportTimeoutError:
                time.sleep(IDLE_POLL_INTERVAL_S)
                continue
            if status.errors:
                msg = "Printer reported errors while waiting: " + ", ".join(
                    status.errors
                )
                pytest.fail(msg)
            return

    pytest.fail(f"Timed out after {STATUS_POLL_TIMEOUT_MS} ms waiting for status reply")


def _wait_for_printer_idle(printer: PrinterInfo) -> None:
    """Poll status until the printer returns to the editing (idle) phase."""
    deadline = time.monotonic() + IDLE_WAIT_TIMEOUT_MS / 1000.0

    with UsbTransport(printer) as transport:
        while time.monotonic() < deadline:
            try:
                status = _read_status(transport)
            except TransportTimeoutError:
                time.sleep(IDLE_POLL_INTERVAL_S)
                continue
            if status.errors:
                msg = "Printer reported errors while waiting: " + ", ".join(
                    status.errors
                )
                pytest.fail(msg)
            if status.phase_type == PhaseType.EDITING:
                return
            time.sleep(IDLE_POLL_INTERVAL_S)

    pytest.fail(
        f"Timed out after {IDLE_WAIT_TIMEOUT_MS} ms waiting for printer to become idle"
    )


def _query_loaded_tape(
    printer: PrinterInfo,
    *,
    require_laminated: bool = False,
) -> TapeWidth:
    with UsbTransport(printer) as transport:
        status = _read_status(transport)

    if status.media_width is None:
        pytest.skip("No tape width reported; load a TZe tape to run hardware tests")

    if status.errors:
        pytest.skip("Printer reported errors: " + ", ".join(status.errors))

    if require_laminated and status.media_type != MediaType.LAMINATED:
        pytest.skip(
            "Half-cut hardware test requires laminated tape; loaded media is "
            f"{status.media_type.name.replace('_', ' ').lower()}"
        )

    return status.media_width


def _fixture_for_tape(mapping: dict[TapeWidth, Path], loaded_tape: TapeWidth) -> Path:
    path = mapping.get(loaded_tape)
    if path is None or not path.is_file():
        pytest.skip(f"No committed fixture for {loaded_tape.mm:g} mm tape")
    return path


@pytest.fixture(scope="module")
def printer() -> PrinterInfo:
    printers = discover()
    assert printers, PRINTER_REQUIRED_MSG
    return printers[0]


@pytest.fixture(scope="module")
def loaded_tape(printer: PrinterInfo) -> TapeWidth:
    return _query_loaded_tape(printer)


@pytest.fixture(scope="module")
def laminated_tape(printer: PrinterInfo) -> TapeWidth:
    return _query_loaded_tape(printer, require_laminated=True)


@pytest.fixture(scope="module")
def label_fixture_path(loaded_tape: TapeWidth) -> Path:
    return _fixture_for_tape(_LABEL_FIXTURES, loaded_tape)


@pytest.fixture(scope="module")
def wrong_tape_width(loaded_tape: TapeWidth) -> TapeWidth:
    """Any tape width different from the loaded tape (for mismatch guard tests)."""
    for width in TapeWidth:
        if width != loaded_tape:
            return width
    pytest.skip("Only one tape width enum value available")
