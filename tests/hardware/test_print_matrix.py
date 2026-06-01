"""Opt-in hardware print matrix test for pre-computed QR fixtures.

These tests physically print labels with different option combinations.
They are skipped unless ``BROTHER_PRINTER_HARDWARE=1`` is set. Run with::

    just test-hardware tests/hardware/test_print_matrix.py

Each parametrized case consumes tape. Requires USB passthrough, udev
permissions, and a loaded TZe tape matching a committed fixture.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from PIL import Image

from brother_printer import print_image
from brother_printer.protocol import STATUS_REPLY_SIZE, decode_status, status_request
from brother_printer.protocol.enums import PhaseType, TapeWidth
from brother_printer.transport import UsbTransport, discover
from brother_printer.transport.base import PrinterInfo

_HARDWARE_ENABLED = os.environ.get("BROTHER_PRINTER_HARDWARE") == "1"
_STATUS_READ_TIMEOUT_MS = 15_000
_IDLE_WAIT_TIMEOUT_MS = 60_000
_IDLE_POLL_INTERVAL_S = 0.5
_ASSETS_DIR = Path(__file__).resolve().parent / "assets"

_TAPE_FIXTURES: dict[TapeWidth, Path] = {
    TapeWidth.MM_3_5: _ASSETS_DIR / "qr_3.5mm.png",
    TapeWidth.MM_6: _ASSETS_DIR / "qr_6mm.png",
    TapeWidth.MM_9: _ASSETS_DIR / "qr_9mm.png",
    TapeWidth.MM_12: _ASSETS_DIR / "qr_12mm.png",
    TapeWidth.MM_18: _ASSETS_DIR / "qr_18mm.png",
    TapeWidth.MM_24: _ASSETS_DIR / "qr_24mm.png",
    TapeWidth.MM_36: _ASSETS_DIR / "qr_36mm.png",
}

pytestmark = [
    pytest.mark.hardware,
    pytest.mark.skipif(
        not _HARDWARE_ENABLED,
        reason="set BROTHER_PRINTER_HARDWARE=1 to run hardware print matrix tests",
    ),
]


def _read_status(transport: UsbTransport):
    transport.write(status_request())
    reply = transport.read_exact(STATUS_REPLY_SIZE, timeout_ms=_STATUS_READ_TIMEOUT_MS)
    return decode_status(reply)


def _wait_for_printer_idle(printer: PrinterInfo) -> None:
    """Poll status until the printer returns to the editing (idle) phase."""
    deadline = time.monotonic() + _IDLE_WAIT_TIMEOUT_MS / 1000.0

    with UsbTransport(printer) as transport:
        while time.monotonic() < deadline:
            status = _read_status(transport)
            if status.errors:
                msg = "Printer reported errors while waiting: " + ", ".join(
                    status.errors
                )
                pytest.fail(msg)
            if status.phase_type == PhaseType.EDITING:
                return
            time.sleep(_IDLE_POLL_INTERVAL_S)

    pytest.fail(
        f"Timed out after {_IDLE_WAIT_TIMEOUT_MS} ms waiting for printer to become idle"
    )


def _query_loaded_tape(printer: PrinterInfo) -> TapeWidth:
    with UsbTransport(printer) as transport:
        status = _read_status(transport)

    if status.media_width is None:
        pytest.skip("No tape width reported; load a TZe tape to run print matrix")

    if status.errors:
        pytest.skip("Printer reported errors: " + ", ".join(status.errors))

    return status.media_width


@pytest.fixture(scope="module")
def printer() -> PrinterInfo:
    printers = discover()
    assert printers, (
        "No PT-E920BT found. Confirm the printer is connected and powered, "
        "USB passthrough is configured, and udev permissions are set "
        "(see docs/install/linux-usb.md)."
    )
    return printers[0]


@pytest.fixture(scope="module")
def loaded_tape(printer: PrinterInfo) -> TapeWidth:
    return _query_loaded_tape(printer)


@pytest.fixture(scope="module")
def fixture_path(loaded_tape: TapeWidth) -> Path:
    path = _TAPE_FIXTURES.get(loaded_tape)
    if path is None or not path.is_file():
        pytest.skip(f"No committed fixture for {loaded_tape.mm:g} mm tape")
    return path


@pytest.mark.parametrize("rotate", [0, 90])
@pytest.mark.parametrize("auto_cut", [True, False])
def test_print_matrix(
    fixture_path: Path,
    loaded_tape: TapeWidth,
    printer: PrinterInfo,
    rotate: int,
    auto_cut: bool,
) -> None:
    """print_image() prints the matching QR fixture with varied options."""
    _wait_for_printer_idle(printer)

    with Image.open(fixture_path) as image:
        written = print_image(
            image.copy(),
            loaded_tape,
            rotate=rotate,
            auto_cut=auto_cut,
        )

    assert written > 0
