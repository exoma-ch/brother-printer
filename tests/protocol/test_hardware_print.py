"""Opt-in hardware print test for a real PT-E920BT.

These tests send a minimal raster job over USB and physically print a
short label. They are skipped unless ``BROTHER_PRINTER_HARDWARE=1`` is set.
Run them with::

    just test-hardware

They require USB passthrough into the devcontainer (see
docs/install/linux-usb.md), the libusb backend, and a loaded TZe tape.
Each run consumes a small amount of tape.
"""

import os

import pytest

from brother_printer.protocol import (
    RASTER_LINE_BYTES,
    STATUS_REPLY_SIZE,
    decode_status,
    encode_job,
    status_request,
)
from brother_printer.transport import UsbTransport, discover

_HARDWARE_ENABLED = os.environ.get("BROTHER_PRINTER_HARDWARE") == "1"

# At least 57 raster lines (4 mm) per vendor minimum print length for TZe tape.
_PRINT_LINE_COUNT = 60
_BLACK_LINE = b"\xff" * RASTER_LINE_BYTES

pytestmark = [
    pytest.mark.hardware,
    pytest.mark.skipif(
        not _HARDWARE_ENABLED,
        reason="set BROTHER_PRINTER_HARDWARE=1 to run hardware print tests",
    ),
]


def test_print_label():
    """encode_job() over USB prints a small label on the loaded tape width."""
    printers = discover()
    assert printers, (
        "No PT-E920BT found. Confirm the printer is connected and powered, "
        "USB passthrough is configured, and udev permissions are set "
        "(see docs/install/linux-usb.md)."
    )

    with UsbTransport(printers[0]) as transport:
        transport.write(status_request())
        reply = transport.read_exact(STATUS_REPLY_SIZE, timeout_ms=5000)
        status = decode_status(reply)

        if status.media_width is None:
            pytest.skip("No tape width reported; load a TZe tape to run print test")

        if status.errors:
            pytest.skip("Printer reported errors: " + ", ".join(status.errors))

        raster_lines = [_BLACK_LINE] * _PRINT_LINE_COUNT
        job = encode_job(status.media_width, raster_lines, no_chain=True)
        written = transport.write(job)

    assert written == len(job)
