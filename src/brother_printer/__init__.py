"""Brother PT-E920BT label printer library and CLI."""

from brother_printer.printing import (
    HalfCutNotSupportedError,
    PrintError,
    PrinterNotReadyError,
    TapeMismatchError,
    print_image,
    print_strip,
    print_text,
    query_status,
    select_printer,
)
from brother_printer.protocol.decoder import PrinterStatus
from brother_printer.protocol.enums import TapeWidth
from brother_printer.transport import PrinterInfo, discover
from brother_printer.transport.errors import (
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
    "print_strip",
    "print_text",
    "query_status",
    "select_printer",
]
