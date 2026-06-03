"""Brother PT-E920BT label printer library and CLI."""

from brother_printer.printing import (
    HalfCutNotSupportedError,
    PrintError,
    PrinterNotReadyError,
    TapeMismatchError,
    print_image,
    print_strip,
)
from brother_printer.protocol.enums import TapeWidth
from brother_printer.transport import PrinterInfo, discover

__version__ = "0.1.0"

discover_printers = discover

__all__ = [
    "HalfCutNotSupportedError",
    "PrintError",
    "PrinterInfo",
    "PrinterNotReadyError",
    "TapeMismatchError",
    "TapeWidth",
    "__version__",
    "discover_printers",
    "print_image",
    "print_strip",
]
