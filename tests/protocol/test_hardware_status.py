"""Opt-in hardware protocol test for a real PT-E920BT.

These tests send raster commands over USB and are skipped unless
``BROTHER_PRINTER_HARDWARE=1`` is set. Run them with::

    just test-hardware

They require USB passthrough into the devcontainer (see
docs/install/linux-usb.md) and the libusb backend.
"""

import os

import pytest

from brother_printer.protocol import (
    STATUS_REPLY_SIZE,
    StatusType,
    TapeWidth,
    decode_status,
    status_request,
)
from brother_printer.transport import UsbTransport, discover

_HARDWARE_ENABLED = os.environ.get("BROTHER_PRINTER_HARDWARE") == "1"

pytestmark = [
    pytest.mark.hardware,
    pytest.mark.skipif(
        not _HARDWARE_ENABLED,
        reason="set BROTHER_PRINTER_HARDWARE=1 to run hardware connectivity tests",
    ),
]


def test_status_request_round_trip():
    """status_request() over USB returns a decodable 32-byte status reply."""
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
    assert status.status_type == StatusType.REPLY
    assert status.media_width is None or isinstance(status.media_width, TapeWidth)
