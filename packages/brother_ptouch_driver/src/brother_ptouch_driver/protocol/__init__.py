"""P-touch raster protocol: pure encode/decode functions.

See docs/vendor/ptouch-raster-command-reference.md and issue #5.
"""

from brother_ptouch_driver.protocol.constants import (
    RASTER_LINE_BYTES,
    STATUS_REPLY_SIZE,
    STATUS_USB_READ_SIZE,
)
from brother_ptouch_driver.protocol.decoder import (
    PrinterStatus,
    decode_status,
    extract_status_reply,
)
from brother_ptouch_driver.protocol.encoder import (
    advanced_mode,
    cut_each,
    eject,
    encode_job,
    encode_strip_job,
    initialize,
    invalidate,
    print_information,
    print_page,
    raster_line,
    select_compression,
    set_margin,
    set_mode,
    status_request,
    switch_raster_mode,
    zero_raster,
)
from brother_ptouch_driver.protocol.enums import (
    ErrorInfo1,
    ErrorInfo2,
    MediaType,
    Notification,
    PhaseType,
    StatusType,
    TapeColor,
    TapeWidth,
    decode_error_messages,
)

__all__ = [
    "ErrorInfo1",
    "ErrorInfo2",
    "MediaType",
    "Notification",
    "PhaseType",
    "PrinterStatus",
    "RASTER_LINE_BYTES",
    "STATUS_REPLY_SIZE",
    "STATUS_USB_READ_SIZE",
    "StatusType",
    "TapeColor",
    "TapeWidth",
    "advanced_mode",
    "cut_each",
    "decode_error_messages",
    "decode_status",
    "extract_status_reply",
    "eject",
    "encode_job",
    "encode_strip_job",
    "initialize",
    "invalidate",
    "print_information",
    "print_page",
    "raster_line",
    "select_compression",
    "set_margin",
    "set_mode",
    "status_request",
    "switch_raster_mode",
    "zero_raster",
]
