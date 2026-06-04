"""Opt-in hardware connectivity tests for a real PT-E920BT.

Run with::

    just test-hardware packages/brother_printer/tests/hardware/test_connectivity.py

Requires USB passthrough and udev permissions (see docs/install/linux-usb.md).
Non-destructive: no tape is consumed.
"""

from brother_printer.transport import UsbTransport, discover

from tests.hardware.conftest import HARDWARE_PYTESTMARK as pytestmark  # noqa: F401


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
