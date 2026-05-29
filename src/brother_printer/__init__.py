"""Brother PT-E920BT label printer library and CLI."""

from brother_printer.transport import PrinterInfo, discover

__version__ = "0.1.0"

discover_printers = discover

__all__ = ["PrinterInfo", "__version__", "discover_printers"]
