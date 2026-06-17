"""P-touch protocol enumerations and error decoding.

See docs/vendor/ptouch-raster-command-reference.md and docs/vendor/tze-tape-widths.md.
"""

from enum import IntEnum, IntFlag


class TapeWidth(IntEnum):
    """TZe media width byte values (status reply table 3, ESC i z n3)."""

    MM_3_5 = 0x04
    MM_6 = 0x06
    MM_9 = 0x09
    MM_12 = 0x0C
    MM_18 = 0x12
    MM_24 = 0x18
    MM_36 = 0x24

    @property
    def mm(self) -> float:
        """Tape width in millimeters."""
        return _TAPE_WIDTH_MM[self]

    @property
    def print_area_pins(self) -> int:
        """Printable pin count at 360 dpi (docs/vendor/tze-tape-widths.md)."""
        return _TAPE_WIDTH_PINS[self]

    @property
    def print_area_left_pins(self) -> int:
        """Left margin pin count at 360 dpi (docs/vendor/tze-tape-widths.md)."""
        return _TAPE_WIDTH_LEFT_PINS[self]

    @classmethod
    def from_byte(cls, value: int) -> "TapeWidth | None":
        """Map a status-reply media-width byte; None means no tape or unknown."""
        if value == 0x00:
            return None
        try:
            return cls(value)
        except ValueError:
            return None


_TAPE_WIDTH_MM: dict[TapeWidth, float] = {
    TapeWidth.MM_3_5: 3.5,
    TapeWidth.MM_6: 6.0,
    TapeWidth.MM_9: 9.0,
    TapeWidth.MM_12: 12.0,
    TapeWidth.MM_18: 18.0,
    TapeWidth.MM_24: 24.0,
    TapeWidth.MM_36: 36.0,
}

_TAPE_WIDTH_PINS: dict[TapeWidth, int] = {
    TapeWidth.MM_3_5: 48,
    TapeWidth.MM_6: 64,
    TapeWidth.MM_9: 106,
    TapeWidth.MM_12: 150,
    TapeWidth.MM_18: 234,
    TapeWidth.MM_24: 320,
    TapeWidth.MM_36: 454,
}

_TAPE_WIDTH_LEFT_PINS: dict[TapeWidth, int] = {
    TapeWidth.MM_3_5: 248,
    TapeWidth.MM_6: 240,
    TapeWidth.MM_9: 219,
    TapeWidth.MM_12: 197,
    TapeWidth.MM_18: 155,
    TapeWidth.MM_24: 112,
    TapeWidth.MM_36: 45,
}


class MediaType(IntEnum):
    """Media type byte (status reply table 4)."""

    NO_MEDIA = 0x00
    LAMINATED = 0x01
    NON_LAMINATED = 0x03
    FABRIC = 0x04
    HEAT_SHRINK_2_1 = 0x11
    FILE_TAPE = 0x13
    FLEXIBLE_ID = 0x14
    SATIN = 0x15
    # Not in Brother's published P900 table; reported by hardware in the field
    # (self-laminating 24/36 mm tape). See issue #39.
    SELF_LAMINATING = 0x16
    HEAT_SHRINK_3_1 = 0x17
    INCOMPATIBLE = 0xFF


class TapeColor(IntEnum):
    """Tape color information byte (status reply table 8)."""

    NO_TAPE = 0x00
    WHITE = 0x01
    OTHER = 0x02
    CLEAR = 0x03
    RED = 0x04
    BLUE = 0x05
    YELLOW = 0x06
    GREEN = 0x07
    BLACK = 0x08
    CLEAR_WHITE_TEXT = 0x09
    MATTE_WHITE = 0x20
    MATTE_CLEAR = 0x21
    MATTE_SILVER = 0x22
    SATIN_GOLD = 0x23
    SATIN_SILVER = 0x24
    BLUE_D = 0x30
    RED_D = 0x31
    FLUORESCENT_ORANGE = 0x40
    FLUORESCENT_YELLOW = 0x41
    BERRY_PINK_S = 0x50
    LIGHT_GRAY_S = 0x51
    LIME_GREEN_S = 0x52
    YELLOW_F = 0x60
    PINK_F = 0x61
    BLUE_F = 0x62
    WHITE_HEAT_SHRINK = 0x70
    # Not in Brother's published colour table; reported by hardware in the field
    # for white self-laminating tape (TZe-SL251). The plain laminated white
    # tape (TZe-S251) reports WHITE (0x01) on the same printer, so 0x80 is the
    # self-laminating variant. See issue #39.
    WHITE_SELF_LAMINATING = 0x80
    WHITE_FLEX_ID = 0x90
    YELLOW_FLEX_ID = 0x91
    CLEANING = 0xF0
    STENCIL = 0xF1
    INCOMPATIBLE = 0xFF


class StatusType(IntEnum):
    """Status type byte (status reply table 5)."""

    REPLY = 0x00
    PRINTING_COMPLETED = 0x01
    ERROR = 0x02
    TURNED_OFF = 0x04
    NOTIFICATION = 0x05
    PHASE_CHANGE = 0x06


class PhaseType(IntEnum):
    """Phase type byte (status reply table 6)."""

    EDITING = 0x00
    PRINTING = 0x01


class Notification(IntEnum):
    """Notification number byte (status reply table 7)."""

    NOT_AVAILABLE = 0x00
    COVER_OPEN = 0x01
    COVER_CLOSED = 0x02
    COOLING_STARTED = 0x03
    COOLING_FINISHED = 0x04


class ErrorInfo1(IntFlag):
    """Error information 1 bitmask (status reply table 1)."""

    NO_MEDIA = 0x01
    END_OF_MEDIA = 0x02
    CUTTER_JAM = 0x04
    WEAK_BATTERIES = 0x08
    PRINTER_IN_USE = 0x10
    HIGH_VOLTAGE_ADAPTER = 0x40


class ErrorInfo2(IntFlag):
    """Error information 2 bitmask (status reply table 2)."""

    REPLACE_MEDIA = 0x01
    EXPANSION_BUFFER_FULL = 0x02
    COMMUNICATION_ERROR = 0x04
    COMMUNICATION_BUFFER_FULL = 0x08
    COVER_OPEN = 0x10
    OVERHEATING = 0x20
    BLACK_MARK_NOT_DETECTED = 0x40
    SYSTEM_ERROR = 0x80


_ERROR1_MESSAGES: dict[ErrorInfo1, str] = {
    ErrorInfo1.NO_MEDIA: "No media",
    ErrorInfo1.END_OF_MEDIA: "End of media",
    ErrorInfo1.CUTTER_JAM: "Cutter jam",
    ErrorInfo1.WEAK_BATTERIES: "Weak batteries",
    ErrorInfo1.PRINTER_IN_USE: "Printer in use",
    ErrorInfo1.HIGH_VOLTAGE_ADAPTER: "High-voltage adapter",
}

_ERROR2_MESSAGES: dict[ErrorInfo2, str] = {
    ErrorInfo2.REPLACE_MEDIA: "Replace media",
    ErrorInfo2.EXPANSION_BUFFER_FULL: "Expansion buffer full",
    ErrorInfo2.COMMUNICATION_ERROR: "Communication error",
    ErrorInfo2.COMMUNICATION_BUFFER_FULL: "Communication buffer full",
    ErrorInfo2.COVER_OPEN: "Cover open",
    ErrorInfo2.OVERHEATING: "Overheating",
    ErrorInfo2.BLACK_MARK_NOT_DETECTED: "Black marking not detected",
    ErrorInfo2.SYSTEM_ERROR: "System error",
}


def decode_error_messages(
    error1: int | ErrorInfo1,
    error2: int | ErrorInfo2,
) -> tuple[str, ...]:
    """Decode error information bytes into human-readable messages."""
    flags1 = ErrorInfo1(error1) if error1 else ErrorInfo1(0)
    flags2 = ErrorInfo2(error2) if error2 else ErrorInfo2(0)
    messages: list[str] = []
    for flag, table in ((flags1, _ERROR1_MESSAGES), (flags2, _ERROR2_MESSAGES)):
        for bit, text in table.items():
            if flag & bit:
                messages.append(text)
    return tuple(messages)
