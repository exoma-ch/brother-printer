"""USB transport for Brother P-touch printers on Linux."""

from usb.core import USBError

from brother_printer.transport.errors import (
    DeviceBusyError,
    DeviceNotFoundError,
    PermissionDeniedError,
    TransportError,
    TransportTimeoutError,
)

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
