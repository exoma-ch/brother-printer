"""Tests for transport error mapping and exception messages."""

import pytest

from brother_printer.transport.errors import (
    DeviceBusyError,
    DeviceNotFoundError,
    PermissionDeniedError,
    TransportError,
    TransportTimeoutError,
)


class _FakeUSBError(Exception):
    """Minimal stand-in for pyusb USBError in unit tests."""

    def __init__(self, err: int | None = None, strerror: str = "") -> None:
        self.errno = err
        self.strerror = strerror
        super().__init__(strerror or f"USBError {err}")


def test_permission_denied_error_includes_udev_hint():
    """PermissionDeniedError points users to udev setup."""
    err = PermissionDeniedError("access denied")
    message = str(err)
    assert "access denied" in message
    assert "udev" in message.lower()
    assert "99-brother-ptouch.rules" in message


def test_transport_error_hierarchy():
    """Transport errors inherit from TransportError."""
    assert issubclass(DeviceNotFoundError, TransportError)
    assert issubclass(PermissionDeniedError, TransportError)
    assert issubclass(DeviceBusyError, TransportError)
    assert issubclass(TransportTimeoutError, TransportError)


@pytest.mark.parametrize(
    ("errno", "expected_type"),
    [
        (2, DeviceNotFoundError),
        (13, PermissionDeniedError),
        (16, DeviceBusyError),
        (110, TransportTimeoutError),
    ],
)
def test_map_usb_error_by_errno(errno, expected_type):
    """USB errno values map to the correct transport exception."""
    from brother_printer.transport.usb import map_usb_error

    exc = _FakeUSBError(err=errno, strerror=f"errno {errno}")
    mapped = map_usb_error(exc)  # type: ignore[arg-type]
    assert isinstance(mapped, expected_type)


def test_map_usb_error_timeout_by_message():
    """Timeout USB errors are detected from the error message."""
    from brother_printer.transport.usb import map_usb_error

    exc = _FakeUSBError(err=None, strerror="Operation timed out")
    mapped = map_usb_error(exc)  # type: ignore[arg-type]
    assert isinstance(mapped, TransportTimeoutError)


def test_map_usb_error_generic_fallback():
    """Unknown USB errors become generic TransportError."""
    from brother_printer.transport.usb import map_usb_error

    exc = _FakeUSBError(err=999, strerror="unknown failure")
    mapped = map_usb_error(exc)  # type: ignore[arg-type]
    assert type(mapped) is TransportError
    assert "unknown failure" in str(mapped)
