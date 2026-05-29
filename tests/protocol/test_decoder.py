"""Tests for P-touch raster protocol status decoder."""

from pathlib import Path

import pytest

from brother_printer.protocol.decoder import decode_status
from brother_printer.protocol.enums import (
    MediaType,
    Notification,
    PhaseType,
    StatusType,
    TapeColor,
    TapeWidth,
)

_GOLDEN_DIR = Path(__file__).parent / "golden"


def _load_golden(name: str) -> bytes:
    return (_GOLDEN_DIR / name).read_bytes()


def _build_status(
    *,
    error1: int = 0,
    error2: int = 0,
    media_width: int = 0x18,
    media_type: int = 0x01,
    status_type: int = 0x00,
    phase_type: int = 0x00,
    phase_hi: int = 0x00,
    phase_lo: int = 0x00,
    notification: int = 0x00,
    tape_color: int = 0x01,
) -> bytes:
    """Build a 32-byte status reply with documented header fields."""
    data = bytearray(32)
    data[0] = 0x80
    data[1] = 0x20
    data[2] = ord("B")
    data[3] = ord("0")
    data[4] = ord("x")
    data[5] = ord("0")
    data[8] = error1
    data[9] = error2
    data[10] = media_width
    data[11] = media_type
    data[18] = status_type
    data[19] = phase_type
    data[20] = phase_hi
    data[21] = phase_lo
    data[22] = notification
    data[24] = tape_color
    return bytes(data)


def test_decode_status_golden():
    """decode_status() parses the golden ready-status reply."""
    status = decode_status(_load_golden("status_ready_24mm.bin"))
    assert status.media_width == TapeWidth.MM_24
    assert status.media_type == MediaType.LAMINATED
    assert status.errors == ()
    assert status.status_type == StatusType.REPLY
    assert status.phase_type == PhaseType.EDITING
    assert status.phase_number == 0
    assert status.notification == Notification.NOT_AVAILABLE
    assert status.tape_color == TapeColor.WHITE


def test_decode_status_no_media():
    """decode_status() returns None width when no tape is loaded."""
    status = decode_status(_build_status(media_width=0x00, media_type=0x00))
    assert status.media_width is None
    assert status.media_type == MediaType.NO_MEDIA


def test_decode_status_errors():
    """decode_status() decodes error bitmask bytes to readable messages."""
    status = decode_status(_build_status(error1=0x01, error2=0x10))
    assert "No media" in status.errors
    assert "Cover open" in status.errors


def test_decode_status_phase_number():
    """decode_status() combines phase high/low bytes into a 16-bit number."""
    status = decode_status(_build_status(phase_hi=0x00, phase_lo=0x01))
    assert status.phase_number == 1


def test_decode_status_rejects_wrong_length():
    """decode_status() requires exactly 32 bytes."""
    with pytest.raises(ValueError, match="32 bytes"):
        decode_status(b"\x80\x20" + b"\x00" * 10)


def test_decode_status_rejects_bad_header():
    """decode_status() validates print-head mark and size bytes."""
    bad = bytearray(_build_status())
    bad[0] = 0x00
    with pytest.raises(ValueError, match="header"):
        decode_status(bytes(bad))


def test_printer_status_is_frozen():
    """PrinterStatus is an immutable value object."""
    status = decode_status(_build_status())
    with pytest.raises(AttributeError):
        status.media_width = TapeWidth.MM_6  # type: ignore[misc]
