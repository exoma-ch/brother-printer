"""Tests for P-touch protocol enums."""

import pytest

from brother_printer.protocol.enums import (
    ErrorInfo1,
    ErrorInfo2,
    MediaType,
    TapeWidth,
    decode_error_messages,
)


@pytest.mark.parametrize(
    ("width", "mm", "pins", "left_pins", "byte_val"),
    [
        (TapeWidth.MM_3_5, 3.5, 48, 248, 0x04),
        (TapeWidth.MM_6, 6, 64, 240, 0x06),
        (TapeWidth.MM_9, 9, 106, 219, 0x09),
        (TapeWidth.MM_12, 12, 150, 197, 0x0C),
        (TapeWidth.MM_18, 18, 234, 155, 0x12),
        (TapeWidth.MM_24, 24, 320, 112, 0x18),
        (TapeWidth.MM_36, 36, 454, 45, 0x24),
    ],
)
def test_tape_width_properties(width, mm, pins, left_pins, byte_val):
    """TapeWidth maps to spec byte values and printable pin counts."""
    assert width.value == byte_val
    assert width.mm == mm
    assert width.print_area_pins == pins
    assert width.print_area_left_pins == left_pins


def test_tape_width_from_byte():
    """TapeWidth.from_byte returns None for no tape and known widths."""
    assert TapeWidth.from_byte(0x00) is None
    assert TapeWidth.from_byte(0x18) is TapeWidth.MM_24
    assert TapeWidth.from_byte(0xFF) is None


def test_media_type_values():
    """MediaType values match status reply table (4)."""
    assert MediaType.NO_MEDIA == 0x00
    assert MediaType.LAMINATED == 0x01
    assert MediaType.NON_LAMINATED == 0x03
    assert MediaType.INCOMPATIBLE == 0xFF


def test_decode_error_messages():
    """Error bytes decode to human-readable strings."""
    errors = decode_error_messages(ErrorInfo1.NO_MEDIA, ErrorInfo2.COVER_OPEN)
    assert "No media" in errors
    assert "Cover open" in errors
