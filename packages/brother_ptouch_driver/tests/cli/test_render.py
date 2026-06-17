"""Tests for CLI status rendering."""

import pytest

from brother_ptouch_driver.cli.render import render_status, status_has_errors
from brother_ptouch_driver.protocol.decoder import PrinterStatus
from brother_ptouch_driver.protocol.enums import (
    MediaType,
    Notification,
    PhaseType,
    StatusType,
    TapeColor,
    TapeWidth,
)
from brother_ptouch_driver.transport.base import PrinterInfo


def _sample_printer() -> PrinterInfo:
    return PrinterInfo(
        vendor_id=0x04F9,
        product_id=0x20C7,
        serial="000123456789",
        product="PT-E920BT",
        bus=1,
        address=5,
    )


def test_status_has_errors_when_error_list_nonempty():
    """status_has_errors() is true when errors are present."""
    status = PrinterStatus(
        media_width=TapeWidth.MM_24,
        media_type=MediaType.LAMINATED,
        errors=("Cover open",),
        status_type=StatusType.REPLY,
        phase_type=PhaseType.EDITING,
        phase_number=0,
        notification=Notification.NOT_AVAILABLE,
        tape_color=TapeColor.WHITE,
    )
    assert status_has_errors(status) is True


def test_render_status_shows_no_tape_when_width_missing():
    """render_status() shows 'No tape' when media_width is None."""
    status = PrinterStatus(
        media_width=None,
        media_type=MediaType.NO_MEDIA,
        errors=(),
        status_type=StatusType.REPLY,
        phase_type=PhaseType.EDITING,
        phase_number=0,
        notification=Notification.NOT_AVAILABLE,
        tape_color=TapeColor.WHITE,
    )
    output = render_status(_sample_printer(), status)
    assert "Tape:       No tape" in output


def test_render_status_shows_no_tape_color():
    """render_status() renders the NO_TAPE colour as 'No tape'."""
    status = PrinterStatus(
        media_width=None,
        media_type=MediaType.NO_MEDIA,
        errors=(),
        status_type=StatusType.REPLY,
        phase_type=PhaseType.EDITING,
        phase_number=0,
        notification=Notification.NOT_AVAILABLE,
        tape_color=TapeColor.NO_TAPE,
    )
    output = render_status(_sample_printer(), status)
    assert "Color:      No tape" in output


def test_render_status_self_laminating_media():
    """render_status() renders the self-laminating media type with a friendly name."""
    status = PrinterStatus(
        media_width=TapeWidth.MM_24,
        media_type=MediaType.SELF_LAMINATING,
        errors=(),
        status_type=StatusType.REPLY,
        phase_type=PhaseType.EDITING,
        phase_number=0,
        notification=Notification.NOT_AVAILABLE,
        tape_color=TapeColor.WHITE,
    )
    output = render_status(_sample_printer(), status)
    assert "Media:      Self Laminating" in output


@pytest.mark.parametrize(
    ("tape_color", "expected"),
    [
        (TapeColor.WHITE_HEAT_SHRINK, "White"),
        (TapeColor.WHITE_SELF_LAMINATING, "White"),
        (TapeColor.WHITE_FLEX_ID, "White"),
        (TapeColor.YELLOW_FLEX_ID, "Yellow"),
    ],
)
def test_render_status_strips_cartridge_suffix_from_colour(tape_color, expected):
    """Colour bytes whose name repeats the cartridge type drop the suffix.

    The cartridge type already appears on the Media line, so e.g. a flexible-ID
    white tape renders ``Color: White`` rather than ``Color: White Flex Id``.
    """
    status = PrinterStatus(
        media_width=TapeWidth.MM_24,
        media_type=MediaType.FLEXIBLE_ID,
        errors=(),
        status_type=StatusType.REPLY,
        phase_type=PhaseType.EDITING,
        phase_number=0,
        notification=Notification.NOT_AVAILABLE,
        tape_color=tape_color,
    )
    output = render_status(_sample_printer(), status)
    assert f"Color:      {expected}\n" in output


def test_render_status_unknown_bytes_degrade_gracefully():
    """render_status() shows undocumented media/colour bytes as 'unknown (0xNN)'."""
    status = PrinterStatus(
        media_width=TapeWidth.MM_24,
        media_type=0x99,
        errors=(),
        status_type=StatusType.REPLY,
        phase_type=PhaseType.EDITING,
        phase_number=0,
        notification=Notification.NOT_AVAILABLE,
        tape_color=0xAB,
    )
    output = render_status(_sample_printer(), status)
    assert "Media:      unknown (0x99)" in output
    assert "Color:      unknown (0xab)" in output
