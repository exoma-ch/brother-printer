"""Tests for UsbTransport open/write/read/close."""

from unittest.mock import MagicMock, call, patch

import pytest
from usb.core import USBError

from brother_printer.transport.base import PrinterInfo
from brother_printer.transport.errors import DeviceNotFoundError, PermissionDeniedError
from brother_printer.transport.usb import UsbTransport


def _printer_info() -> PrinterInfo:
    return PrinterInfo(
        vendor_id=0x04F9,
        product_id=0x20C7,
        serial="000123456789",
        product="PT-E920BT",
        bus=1,
        address=5,
    )


def _make_endpoints():
    """Bulk OUT and IN endpoints matching PT-P900 family layout."""
    ep_out = MagicMock()
    ep_out.bEndpointAddress = 0x02
    ep_out.bmAttributes = 0x02  # bulk
    ep_out.wMaxPacketSize = 64

    ep_in = MagicMock()
    ep_in.bEndpointAddress = 0x81
    ep_in.bmAttributes = 0x02
    ep_in.wMaxPacketSize = 64

    return ep_out, ep_in


def _make_usb_device(*, kernel_active: bool = False):
    device = MagicMock()
    device.is_kernel_driver_active.return_value = kernel_active
    ep_out, ep_in = _make_endpoints()
    config = MagicMock()
    interface = MagicMock()
    interface.__iter__ = MagicMock(return_value=iter([ep_out, ep_in]))
    config.__getitem__.return_value = interface
    device.get_active_configuration.return_value = config
    return device, ep_out, ep_in


@patch("brother_printer.transport.usb.usb.util.release_interface")
@patch("brother_printer.transport.usb.usb.util.claim_interface")
@patch("brother_printer.transport.usb.usb.core.find")
def test_usb_transport_open_write_read_close(mock_find, mock_claim, mock_release):
    """UsbTransport performs bulk I/O after open."""
    device, ep_out, ep_in = _make_usb_device()
    mock_find.return_value = [device]
    ep_out.write.return_value = 3
    ep_in.read.return_value = b"\x01\x02"

    transport = UsbTransport(_printer_info())
    transport.open()
    assert transport.write(b"\x00\x01\x02") == 3
    assert transport.read(2) == b"\x01\x02"
    transport.close()

    device.set_configuration.assert_called_once()
    mock_claim.assert_called_once_with(device, 0)
    ep_out.write.assert_called_once()
    ep_in.read.assert_called_once()
    mock_release.assert_called_once_with(device, 0)


@patch("brother_printer.transport.usb.usb.util.release_interface")
@patch("brother_printer.transport.usb.usb.util.claim_interface")
@patch("brother_printer.transport.usb.usb.core.find")
def test_usb_transport_detaches_kernel_driver_when_active(
    mock_find, mock_claim, mock_release
):
    """UsbTransport detaches an active kernel driver before claiming."""
    device, _, _ = _make_usb_device(kernel_active=True)
    mock_find.return_value = [device]

    transport = UsbTransport(_printer_info())
    transport.open()
    transport.close()

    device.detach_kernel_driver.assert_called_once_with(0)
    device.assert_has_calls([call.detach_kernel_driver(0), call.set_configuration()])
    mock_claim.assert_called_once_with(device, 0)
    device.attach_kernel_driver.assert_called_once_with(0)


@patch("brother_printer.transport.usb.usb.util.release_interface")
@patch("brother_printer.transport.usb.usb.util.claim_interface")
@patch("brother_printer.transport.usb.usb.core.find")
def test_usb_transport_context_manager(mock_find, mock_claim, mock_release):
    """UsbTransport works as a context manager."""
    device, ep_out, ep_in = _make_usb_device()
    mock_find.return_value = [device]
    ep_out.write.return_value = 1
    ep_in.read.return_value = b"\xff"

    with UsbTransport(_printer_info()) as transport:
        assert transport.write(b"\x00") == 1
        assert transport.read(1) == b"\xff"

    mock_release.assert_called_once_with(device, 0)


@patch("brother_printer.transport.usb.usb.core.find")
def test_usb_transport_open_raises_when_device_missing(mock_find):
    """UsbTransport.open() raises DeviceNotFoundError when device is absent."""
    mock_find.return_value = None
    transport = UsbTransport(_printer_info())

    with pytest.raises(DeviceNotFoundError):
        transport.open()


@patch("brother_printer.transport.usb.usb.util.claim_interface")
@patch("brother_printer.transport.usb.usb.core.find")
def test_usb_transport_write_maps_usb_error(mock_find, mock_claim):
    """UsbTransport.write() maps pyusb errors to transport exceptions."""
    device, ep_out, _ = _make_usb_device()
    mock_find.return_value = [device]
    ep_out.write.side_effect = USBError("Access denied", errno=13)

    transport = UsbTransport(_printer_info())
    transport.open()

    with pytest.raises(PermissionDeniedError):
        transport.write(b"\x00")


@patch("brother_printer.transport.usb.usb.util.claim_interface")
@patch("brother_printer.transport.usb.usb.core.find")
def test_usb_transport_read_respects_timeout(mock_find, mock_claim):
    """UsbTransport.read() passes timeout to bulk IN endpoint."""
    device, _, ep_in = _make_usb_device()
    mock_find.return_value = [device]
    ep_in.read.return_value = b""

    transport = UsbTransport(_printer_info(), default_timeout_ms=500)
    transport.open()
    transport.read(64, timeout_ms=250)

    ep_in.read.assert_called_once_with(64, 250)


@patch("brother_printer.transport.usb.usb.util.release_interface")
@patch("brother_printer.transport.usb.usb.util.claim_interface")
@patch("brother_printer.transport.usb.usb.core.find")
def test_usb_transport_close_is_idempotent(mock_find, mock_claim, mock_release):
    """UsbTransport.close() can be called multiple times safely."""
    device, _, _ = _make_usb_device()
    mock_find.return_value = [device]

    transport = UsbTransport(_printer_info())
    transport.open()
    transport.close()
    transport.close()

    mock_release.assert_called_once()


@patch("brother_printer.transport.usb.usb.util.release_interface")
@patch("brother_printer.transport.usb.usb.util.claim_interface")
@patch("brother_printer.transport.usb.usb.core.find")
def test_usb_transport_read_exact_retries_until_enough_bytes(
    mock_find, mock_claim, mock_release
):
    """read_exact() keeps reading until n bytes arrive (empty reads are retried)."""
    device, ep_out, ep_in = _make_usb_device()
    mock_find.return_value = [device]
    status = b"\x80\x20" + b"\x00" * 30
    ep_in.read.side_effect = [b"", status]

    transport = UsbTransport(_printer_info())
    transport.open()
    assert transport.read_exact(32, timeout_ms=5000) == status
    assert ep_in.read.call_count == 2
    transport.close()
