"""Tests for P-touch protocol enums."""

import pytest

from brother_ptouch_driver.protocol.enums import (
    ErrorInfo1,
    ErrorInfo2,
    MediaType,
    TapeColor,
    TapeWidth,
    decode_error_messages,
    effective_print_pins,
    is_self_laminating,
    self_laminating_band_pins,
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


def test_media_type_self_laminating():
    """MediaType includes the field-reported self-laminating byte (issue #39)."""
    assert MediaType.SELF_LAMINATING == 0x16


def test_self_laminating_band_pins():
    """Band height is a per-width hardware-measured value (issue #50)."""
    assert self_laminating_band_pins(TapeWidth.MM_24) == 120
    assert self_laminating_band_pins(TapeWidth.MM_36) == 156
    # Widths without a measured band fall back to the full print area.
    assert self_laminating_band_pins(TapeWidth.MM_12) == TapeWidth.MM_12.print_area_pins


def test_is_self_laminating_by_media_type_or_color():
    """Self-laminating is detected via media type 0x16 or tape color 0x80."""
    assert is_self_laminating(MediaType.SELF_LAMINATING)
    assert is_self_laminating(MediaType.LAMINATED, TapeColor.WHITE_SELF_LAMINATING)
    assert not is_self_laminating(MediaType.LAMINATED, TapeColor.WHITE)
    # Undocumented raw bytes never look self-laminating.
    assert not is_self_laminating(0x99, 0x99)


@pytest.mark.parametrize(
    ("tape", "media_type", "tape_color", "expected"),
    [
        (TapeWidth.MM_24, MediaType.SELF_LAMINATING, TapeColor.CLEAR, 120),
        (TapeWidth.MM_36, MediaType.SELF_LAMINATING, TapeColor.CLEAR, 156),
        (TapeWidth.MM_24, MediaType.LAMINATED, TapeColor.WHITE_SELF_LAMINATING, 120),
        (TapeWidth.MM_24, MediaType.LAMINATED, TapeColor.WHITE, 320),
        (TapeWidth.MM_36, MediaType.LAMINATED, TapeColor.WHITE, 454),
    ],
)
def test_effective_print_pins(tape, media_type, tape_color, expected):
    """Self-laminating confines to the band; other media use the full print area."""
    assert effective_print_pins(tape, media_type, tape_color) == expected


def test_tape_color_values():
    """TapeColor covers no-tape and documented extended-palette bytes (table 8)."""
    assert TapeColor.NO_TAPE == 0x00
    assert TapeColor.WHITE == 0x01
    assert TapeColor.MATTE_SILVER == 0x22
    assert TapeColor.FLUORESCENT_ORANGE == 0x40
    assert TapeColor.WHITE_FLEX_ID == 0x90
    assert TapeColor.INCOMPATIBLE == 0xFF


def test_decode_error_messages():
    """Error bytes decode to human-readable strings."""
    errors = decode_error_messages(ErrorInfo1.NO_MEDIA, ErrorInfo2.COVER_OPEN)
    assert "No media" in errors
    assert "Cover open" in errors
