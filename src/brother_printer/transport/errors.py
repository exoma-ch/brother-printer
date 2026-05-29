"""Transport-layer exceptions."""


class TransportError(Exception):
    """Base exception for transport failures."""


class DeviceNotFoundError(TransportError):
    """No matching USB device is connected."""


class PermissionDeniedError(TransportError):
    """USB access denied (typically missing udev rules or group membership)."""

    _UDEV_HINT = (
        "Install udev rules for non-root access — see "
        "packaging/udev/99-brother-ptouch.rules and docs/install/linux-usb.md"
    )

    def __str__(self) -> str:
        base = super().__str__()
        if base:
            return f"{base}. {self._UDEV_HINT}"
        return self._UDEV_HINT


class DeviceBusyError(TransportError):
    """USB device is claimed by another driver or process."""


class TransportTimeoutError(TransportError):
    """USB read or write timed out."""
