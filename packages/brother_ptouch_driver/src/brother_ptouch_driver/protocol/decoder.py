"""P-touch raster protocol status decoder — pure bytes in, no I/O.

See docs/vendor/ptouch-raster-command-reference.md.
"""

from dataclasses import dataclass
from enum import IntEnum

from brother_ptouch_driver.protocol.constants import (
    STATUS_HEADER_MARK,
    STATUS_OFFSET_ERROR1,
    STATUS_OFFSET_ERROR2,
    STATUS_OFFSET_MEDIA_TYPE,
    STATUS_OFFSET_MEDIA_WIDTH,
    STATUS_OFFSET_NOTIFICATION,
    STATUS_OFFSET_PHASE_HI,
    STATUS_OFFSET_PHASE_LO,
    STATUS_OFFSET_PHASE_TYPE,
    STATUS_OFFSET_STATUS_TYPE,
    STATUS_OFFSET_TAPE_COLOR,
    STATUS_REPLY_SIZE,
    STATUS_SIZE_BYTE,
)
from brother_ptouch_driver.protocol.enums import (
    MediaType,
    Notification,
    PhaseType,
    StatusType,
    TapeColor,
    TapeWidth,
    decode_error_messages,
)


@dataclass(frozen=True)
class PrinterStatus:
    """Parsed 32-byte status reply from the printer."""

    media_width: TapeWidth | None
    media_type: MediaType | int
    errors: tuple[str, ...]
    status_type: StatusType | int
    phase_type: PhaseType | int
    phase_number: int
    notification: Notification | int
    tape_color: TapeColor | int


def extract_status_reply(data: bytes) -> bytes:
    """Take the 32-byte status payload from a USB bulk IN read buffer."""
    if len(data) < STATUS_REPLY_SIZE:
        msg = f"status buffer must be at least {STATUS_REPLY_SIZE} bytes"
        raise ValueError(msg)
    return data[:STATUS_REPLY_SIZE]


def decode_status(data: bytes) -> PrinterStatus:
    """Parse a 32-byte status reply into a PrinterStatus."""
    if len(data) != STATUS_REPLY_SIZE:
        msg = f"status reply must be exactly {STATUS_REPLY_SIZE} bytes"
        raise ValueError(msg)
    if data[0] != STATUS_HEADER_MARK or data[1] != STATUS_SIZE_BYTE:
        msg = "invalid status reply header"
        raise ValueError(msg)

    error1 = data[STATUS_OFFSET_ERROR1]
    error2 = data[STATUS_OFFSET_ERROR2]
    width_byte = data[STATUS_OFFSET_MEDIA_WIDTH]
    media_type_byte = data[STATUS_OFFSET_MEDIA_TYPE]
    status_type_byte = data[STATUS_OFFSET_STATUS_TYPE]
    phase_type_byte = data[STATUS_OFFSET_PHASE_TYPE]
    phase_number = data[STATUS_OFFSET_PHASE_HI] << 8 | data[STATUS_OFFSET_PHASE_LO]
    notification_byte = data[STATUS_OFFSET_NOTIFICATION]
    tape_color_byte = data[STATUS_OFFSET_TAPE_COLOR]

    return PrinterStatus(
        media_width=TapeWidth.from_byte(width_byte),
        media_type=_enum_from_byte(MediaType, media_type_byte),
        errors=decode_error_messages(error1, error2),
        status_type=_enum_from_byte(StatusType, status_type_byte),
        phase_type=_enum_from_byte(PhaseType, phase_type_byte),
        phase_number=phase_number,
        notification=_enum_from_byte(Notification, notification_byte),
        tape_color=_enum_from_byte(TapeColor, tape_color_byte),
    )


def _enum_from_byte(enum_cls: type[IntEnum], value: int) -> IntEnum | int:
    """Map a status byte to its enum member, or the raw byte if undocumented.

    Status queries must never crash on an unrecognised byte (issue #39); the raw
    int is returned for diagnostics and rendered as ``unknown (0xNN)``.
    """
    try:
        return enum_cls(value)
    except ValueError:
        return value
