"""Tests for CLI status rendering."""

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
