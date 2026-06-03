"""Tests for P-touch raster protocol constants."""

from brother_printer.protocol.constants import (
    HEAD_PINS,
    CMD_ADVANCED_MODE,
    CMD_COMPRESSION,
    CMD_CUT_EACH,
    CMD_EJECT,
    CMD_INITIALIZE,
    CMD_INVALIDATE_COUNT,
    CMD_MARGIN,
    CMD_MODE,
    CMD_PRINT,
    CMD_PRINT_INFO,
    CMD_RASTER,
    CMD_STATUS_REQUEST,
    CMD_SWITCH_RASTER,
    CMD_ZERO_RASTER,
    RASTER_LINE_BYTES,
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


def test_command_opcodes():
    """Command opcodes match docs/vendor/ptouch-raster-command-reference.md."""
    assert CMD_INITIALIZE == b"\x1b\x40"
    assert CMD_STATUS_REQUEST == b"\x1b\x69\x53"
    assert CMD_SWITCH_RASTER == b"\x1b\x69\x61\x01"
    assert CMD_PRINT_INFO == b"\x1b\x69\x7a"
    assert CMD_MODE == b"\x1b\x69\x4d"
    assert CMD_ADVANCED_MODE == b"\x1b\x69\x4b"
    assert CMD_CUT_EACH == b"\x1b\x69\x41"
    assert CMD_MARGIN == b"\x1b\x69\x64"
    assert CMD_COMPRESSION == b"\x4d"
    assert CMD_RASTER == b"\x47"
    assert CMD_ZERO_RASTER == b"\x5a"
    assert CMD_PRINT == b"\x0c"
    assert CMD_EJECT == b"\x1a"


def test_invalidate_count():
    """Invalidate sends 200 null bytes per raster command reference."""
    assert CMD_INVALIDATE_COUNT == 200


def test_raster_line_bytes():
    """Uncompressed raster lines are 70 bytes (560 pins / 8)."""
    assert RASTER_LINE_BYTES == 70


def test_head_pins():
    """Print head width is derived from raster line byte count."""
    assert HEAD_PINS == RASTER_LINE_BYTES * 8
    assert HEAD_PINS == 560


def test_status_reply_layout():
    """Status reply is 32 bytes with documented header and offsets."""
    assert STATUS_REPLY_SIZE == 32
    assert STATUS_HEADER_MARK == 0x80
    assert STATUS_SIZE_BYTE == 0x20
    assert STATUS_OFFSET_ERROR1 == 8
    assert STATUS_OFFSET_ERROR2 == 9
    assert STATUS_OFFSET_MEDIA_WIDTH == 10
    assert STATUS_OFFSET_MEDIA_TYPE == 11
    assert STATUS_OFFSET_STATUS_TYPE == 18
    assert STATUS_OFFSET_PHASE_TYPE == 19
    assert STATUS_OFFSET_PHASE_HI == 20
    assert STATUS_OFFSET_PHASE_LO == 21
    assert STATUS_OFFSET_NOTIFICATION == 22
    assert STATUS_OFFSET_TAPE_COLOR == 24
