"""Tests for USB printer discovery."""

from unittest.mock import MagicMock, patch

from brother_printer.transport.base import PrinterInfo
from brother_printer.transport.usb import (
    BROTHER_VID,
    PT_E920BT_PRODUCT_STRING,
    discover,
)


def _make_device(
    *,
    vendor_id: int = BROTHER_VID,
    product_id: int = 0x20C7,
    product: str = PT_E920BT_PRODUCT_STRING,
    serial: str | None = "000123456789",
    bus: int = 1,
    address: int = 5,
) -> MagicMock:
    """Build a mock pyusb device."""
    device = MagicMock()
    device.idVendor = vendor_id
    device.idProduct = product_id
    device.bus = bus
    device.address = address
    device.iProduct = 2
    device.iSerialNumber = 3
    device._product = product
    device._serial = serial
    return device


def _configure_get_string(mock_get_string, devices: list[MagicMock]) -> None:
    """Wire usb.util.get_string to return product/serial for mock devices."""

    def get_string(device, index):
        if index == device.iProduct:
            return device._product
        if index == device.iSerialNumber:
            return device._serial
        return None

    mock_get_string.side_effect = get_string


@patch("brother_printer.transport.usb.usb.util.get_string")
@patch("brother_printer.transport.usb.usb.core.find")
def test_discover_finds_pt_e920bt(mock_find, mock_get_string):
    """discover() returns PT-E920BT devices matched by product string."""
    device = _make_device()
    mock_find.return_value = [device]
    _configure_get_string(mock_get_string, [device])

    printers = discover()

    mock_find.assert_called_once_with(idVendor=BROTHER_VID, find_all=True)
    assert len(printers) == 1
    info = printers[0]
    assert info.vendor_id == BROTHER_VID
    assert info.product_id == 0x20C7
    assert info.product == PT_E920BT_PRODUCT_STRING
    assert info.serial == "000123456789"
    assert info.bus == 1
    assert info.address == 5
    assert info.identifier == "04f9:20c7#000123456789"


@patch("brother_printer.transport.usb.usb.util.get_string")
@patch("brother_printer.transport.usb.usb.core.find")
def test_discover_filters_non_matching_product_string(mock_find, mock_get_string):
    """discover() ignores Brother devices that are not PT-E920BT."""
    other = _make_device(product="PT-P910BT", product_id=0x20C7)
    target = _make_device(product=PT_E920BT_PRODUCT_STRING, product_id=0x9999)
    mock_find.return_value = [other, target]
    _configure_get_string(mock_get_string, [other, target])

    printers = discover()

    assert len(printers) == 1
    assert printers[0].product_id == 0x9999


@patch("brother_printer.transport.usb.usb.util.get_string")
@patch("brother_printer.transport.usb.usb.core.find")
def test_discover_product_string_match_is_case_insensitive(mock_find, mock_get_string):
    """discover() matches product string case-insensitively."""
    device = _make_device(product="pt-e920bt")
    mock_find.return_value = [device]
    _configure_get_string(mock_get_string, [device])

    assert len(discover()) == 1


@patch("brother_printer.transport.usb.usb.core.find")
def test_discover_returns_empty_when_no_devices(mock_find):
    """discover() returns an empty list when nothing is connected."""
    mock_find.return_value = []
    assert discover() == []


@patch("brother_printer.transport.usb.usb.util.get_string")
@patch("brother_printer.transport.usb.usb.core.find")
def test_discover_skips_devices_without_product_descriptor(mock_find, mock_get_string):
    """discover() skips devices whose product string cannot be read."""
    device = _make_device()
    device.iProduct = 0
    mock_find.return_value = [device]

    assert discover() == []
    mock_get_string.assert_not_called()


@patch("brother_printer.transport.usb.usb.util.get_string")
@patch("brother_printer.transport.usb.usb.core.find")
def test_discover_returns_printer_info_instances(mock_find, mock_get_string):
    """discover() returns frozen PrinterInfo dataclass instances."""
    device = _make_device(serial=None, bus=3, address=9)
    device._serial = None
    mock_find.return_value = [device]
    _configure_get_string(mock_get_string, [device])

    printers = discover()

    assert len(printers) == 1
    assert isinstance(printers[0], PrinterInfo)
    assert printers[0].identifier == "04f9:20c7#3:9"
