"""Opt-in hardware connectivity test for a real PT-E920BT.

These tests talk to a physically connected printer and are skipped unless
``BROTHER_PRINTER_HARDWARE=1`` is set. Run them with::

    just test-hardware

They require USB passthrough into the devcontainer (see
docs/install/linux-usb.md) and the libusb backend.
"""

import os

import pytest

from brother_printer.transport import UsbTransport, discover

_HARDWARE_ENABLED = os.environ.get("BROTHER_PRINTER_HARDWARE") == "1"

pytestmark = [
    pytest.mark.hardware,
    pytest.mark.skipif(
        not _HARDWARE_ENABLED,
        reason="set BROTHER_PRINTER_HARDWARE=1 to run hardware connectivity tests",
    ),
]


def test_discover_finds_connected_printer():
    """discover() returns at least one PT-E920BT when one is connected."""
    printers = discover()
    assert printers, (
        "No PT-E920BT found. Confirm the printer is connected and powered, "
        "USB passthrough is configured, and udev permissions are set "
        "(see docs/install/linux-usb.md)."
    )
    for printer in printers:
        assert printer.product.upper() == "PT-E920BT"
        assert printer.vendor_id == 0x04F9


def test_open_close_round_trip():
    """UsbTransport can claim and release the printer interface."""
    printers = discover()
    assert printers, "No PT-E920BT found; cannot test open/close."

    with UsbTransport(printers[0]):
        pass
