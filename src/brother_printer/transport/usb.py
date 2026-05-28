"""USB transport for Brother P-touch printers on Linux.

USB identifiers: see docs/vendor/usb-ids.md
"""

import usb.core
import usb.util
from usb.core import USBError

from brother_printer.transport.base import PrinterInfo
from brother_printer.transport.errors import (
    DeviceBusyError,
    DeviceNotFoundError,
    PermissionDeniedError,
    TransportError,
    TransportTimeoutError,
)

# Brother Industries, Ltd. — see docs/vendor/usb-ids.md
BROTHER_VID = 0x04F9
PT_E920BT_PRODUCT_STRING = "PT-E920BT"

# errno values from libusb (via pyusb backend)
_ERRNO_ENOENT = 2
_ERRNO_EACCES = 13
_ERRNO_EBUSY = 16
_ERRNO_ETIMEDOUT = 110


def map_usb_error(exc: USBError) -> TransportError:
    """Map a pyusb USBError to a transport-layer exception."""
    errno = getattr(exc, "errno", None)
    message = getattr(exc, "strerror", None) or str(exc)

    if errno == _ERRNO_ENOENT:
        return DeviceNotFoundError(message)
    if errno == _ERRNO_EACCES:
        return PermissionDeniedError(message)
    if errno == _ERRNO_EBUSY:
        return DeviceBusyError(message)
    if errno == _ERRNO_ETIMEDOUT or "timed out" in message.lower():
        return TransportTimeoutError(message)
    return TransportError(message)


def _read_string_descriptor(device: usb.core.Device, index: int) -> str | None:
    """Read a USB string descriptor, returning None on failure."""
    if not index:
        return None
    try:
        return usb.util.get_string(device, index)
    except (USBError, ValueError, UnicodeDecodeError):
        return None


def discover() -> list[PrinterInfo]:
    """List connected PT-E920BT printers on USB."""
    devices = usb.core.find(idVendor=BROTHER_VID, find_all=True) or []
    printers: list[PrinterInfo] = []

    for device in devices:
        product = _read_string_descriptor(device, device.iProduct)
        if not product:
            continue
        if product.strip().lower() != PT_E920BT_PRODUCT_STRING.lower():
            continue

        serial = _read_string_descriptor(device, device.iSerialNumber)
        printers.append(
            PrinterInfo(
                vendor_id=device.idVendor,
                product_id=device.idProduct,
                serial=serial,
                product=product.strip(),
                bus=device.bus,
                address=device.address,
            )
        )

    return printers
