"""Brother PT-E920BT label printer library and CLI."""

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
from brother_ptouch_driver.protocol.enums import TapeWidth
from brother_ptouch_driver.transport import PrinterInfo, discover
from brother_ptouch_driver.transport.errors import (
    DeviceBusyError,
    DeviceNotFoundError,
    PermissionDeniedError,
    TransportError,
    TransportTimeoutError,
)

__version__ = "0.1.0"

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
    "TapeMismatchError",
    "TapeWidth",
    "TransportError",
    "TransportTimeoutError",
    "__version__",
    "discover_printers",
    "print_image",
    "print_png",
    "print_strip",
    "query_status",
    "select_printer",
]
