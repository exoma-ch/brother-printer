"""Brother PT-E920BT label printer library and CLI."""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

from brother_ptouch_driver.imaging.errors import ImageScalingError, ImagingError
from brother_ptouch_driver.printing import (
    HalfCutNotSupportedError,
    PrintError,
    PrinterNotReadyError,
    TapeMismatchError,
    print_image,
    print_png,
    print_strip,
    query_status,
    select_printer,
)
from brother_ptouch_driver.protocol.decoder import PrinterStatus
from brother_ptouch_driver.protocol.enums import (
    TapeColor,
    TapeWidth,
    effective_print_pins,
    is_self_laminating,
    self_laminating_band_pins,
)
from brother_ptouch_driver.transport import PrinterInfo, discover
from brother_ptouch_driver.transport.errors import (
    DeviceBusyError,
    DeviceNotFoundError,
    PermissionDeniedError,
    TransportError,
    TransportTimeoutError,
)

try:
    __version__ = _pkg_version("brother-ptouch-driver")
except PackageNotFoundError:  # pragma: no cover - source tree without install
    __version__ = "0.0.0+unknown"

discover_printers = discover

__all__ = [
    "DeviceBusyError",
    "DeviceNotFoundError",
    "HalfCutNotSupportedError",
    "ImageScalingError",
    "ImagingError",
    "PermissionDeniedError",
    "PrintError",
    "PrinterInfo",
    "PrinterNotReadyError",
    "PrinterStatus",
    "TapeColor",
    "TapeMismatchError",
    "TapeWidth",
    "TransportError",
    "TransportTimeoutError",
    "__version__",
    "discover_printers",
    "effective_print_pins",
    "is_self_laminating",
    "self_laminating_band_pins",
    "print_image",
    "print_png",
    "print_strip",
    "query_status",
    "select_printer",
]
