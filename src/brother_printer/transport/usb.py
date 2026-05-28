"""USB transport for Brother P-touch printers on Linux.

USB identifiers: see docs/vendor/usb-ids.md
"""

import usb.core
import usb.util
from usb.core import NoBackendError, USBError

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
    message = str(getattr(exc, "strerror", None) or exc)

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
    try:
        devices = usb.core.find(idVendor=BROTHER_VID, find_all=True) or []
    except NoBackendError as exc:
        raise TransportError(
            "USB backend unavailable — install libusb-1.0-0 "
            "(see docs/install/linux-usb.md)"
        ) from exc
    except USBError as exc:
        raise map_usb_error(exc) from exc

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


_DEFAULT_INTERFACE = 0
_DEFAULT_TIMEOUT_MS = 5000


class UsbTransport:
    """USB bulk transport for a Brother P-touch printer."""

    def __init__(
        self,
        printer: PrinterInfo,
        *,
        default_timeout_ms: int = _DEFAULT_TIMEOUT_MS,
    ) -> None:
        self._printer = printer
        self._default_timeout_ms = default_timeout_ms
        self._device: usb.core.Device | None = None
        self._ep_out: usb.core.Endpoint | None = None
        self._ep_in: usb.core.Endpoint | None = None
        self._kernel_driver_detached = False
        self._opened = False

    def open(self) -> None:
        """Open the USB device and claim the printer interface."""
        if self._opened:
            return

        device = self._find_device()
        if device is None:
            raise DeviceNotFoundError(
                f"No USB device found for {self._printer.identifier}"
            )

        try:
            device.set_configuration()
            if device.is_kernel_driver_active(_DEFAULT_INTERFACE):
                device.detach_kernel_driver(_DEFAULT_INTERFACE)
                self._kernel_driver_detached = True
            device.claim_interface(_DEFAULT_INTERFACE)
            self._ep_out, self._ep_in = self._resolve_bulk_endpoints(device)
        except USBError as exc:
            raise map_usb_error(exc) from exc

        self._device = device
        self._opened = True

    def close(self) -> None:
        """Release the USB interface and close the device."""
        if not self._opened or self._device is None:
            return

        device = self._device
        try:
            device.release_interface(_DEFAULT_INTERFACE)
            if self._kernel_driver_detached:
                device.attach_kernel_driver(_DEFAULT_INTERFACE)
        except USBError as exc:
            raise map_usb_error(exc) from exc
        finally:
            self._device = None
            self._ep_out = None
            self._ep_in = None
            self._kernel_driver_detached = False
            self._opened = False

    def write(self, data: bytes) -> int:
        """Write bytes to the printer bulk OUT endpoint."""
        self._ensure_open()
        assert self._ep_out is not None
        try:
            return self._ep_out.write(data, self._default_timeout_ms)
        except USBError as exc:
            raise map_usb_error(exc) from exc

    def read(self, n: int, timeout_ms: int | None = None) -> bytes:
        """Read up to n bytes from the printer bulk IN endpoint."""
        self._ensure_open()
        assert self._ep_in is not None
        timeout = self._default_timeout_ms if timeout_ms is None else timeout_ms
        try:
            data = self._ep_in.read(n, timeout)
            return bytes(data)
        except USBError as exc:
            raise map_usb_error(exc) from exc

    def __enter__(self) -> "UsbTransport":
        self.open()
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def _ensure_open(self) -> None:
        if not self._opened:
            raise TransportError("Transport is not open")

    def _find_device(self) -> usb.core.Device | None:
        devices = (
            usb.core.find(
                idVendor=self._printer.vendor_id,
                idProduct=self._printer.product_id,
                find_all=True,
            )
            or []
        )
        if not devices:
            return None

        for device in devices:
            if self._printer.serial:
                serial = _read_string_descriptor(device, device.iSerialNumber)
                if serial == self._printer.serial:
                    return device
            elif (
                device.bus == self._printer.bus
                and device.address == self._printer.address
            ):
                return device

        return devices[0]

    def _resolve_bulk_endpoints(
        self, device: usb.core.Device
    ) -> tuple[usb.core.Endpoint, usb.core.Endpoint]:
        configuration = device.get_active_configuration()
        interface = configuration[(_DEFAULT_INTERFACE, 0)]

        ep_out: usb.core.Endpoint | None = None
        ep_in: usb.core.Endpoint | None = None

        for endpoint in interface:
            if (
                usb.util.endpoint_type(endpoint.bmAttributes)
                != usb.util.ENDPOINT_TYPE_BULK
            ):
                continue
            direction = usb.util.endpoint_direction(endpoint.bEndpointAddress)
            if direction == usb.util.ENDPOINT_OUT:
                ep_out = endpoint
            elif direction == usb.util.ENDPOINT_IN:
                ep_in = endpoint

        if ep_out is None or ep_in is None:
            raise TransportError("Missing bulk IN/OUT endpoints on printer interface")

        return ep_out, ep_in
