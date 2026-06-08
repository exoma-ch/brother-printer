"""Tests for print_text() orchestration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from brother_ptouch_driver import PrintError
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


def _ready_status(*, tape: TapeWidth = TapeWidth.MM_24) -> PrinterStatus:
    return PrinterStatus(
        media_width=tape,
        media_type=MediaType.LAMINATED,
        errors=(),
        status_type=StatusType.REPLY,
        phase_type=PhaseType.EDITING,
        phase_number=0,
        notification=Notification.NOT_AVAILABLE,
        tape_color=TapeColor.WHITE,
    )


def _mock_transport() -> MagicMock:
    transport = MagicMock()
    transport.__enter__ = MagicMock(return_value=transport)
    transport.__exit__ = MagicMock(return_value=False)
    transport.write.return_value = 100
    transport.read_exact.return_value = b"\x00" * 32
    return transport


@patch("brother_ptouch_driver.printing.encode_job")
@patch("brother_ptouch_driver.printing.image_to_raster")
@patch("brother_ptouch_label.printing.render_text")
@patch("brother_ptouch_driver.printing.decode_status")
@patch("brother_ptouch_driver.printing.status_request", return_value=b"\x1biS")
@patch("brother_ptouch_driver.printing.UsbTransport")
@patch("brother_ptouch_driver.printing.discover")
def test_print_text_composes_render_and_raster(
    mock_discover,
    mock_transport_cls,
    mock_status_request,
    mock_decode_status,
    mock_render_text,
    mock_image_to_raster,
    mock_encode_job,
):
    """print_text() renders text then prints with rotation already baked in."""
    from brother_ptouch_label.printing import print_text

    mock_discover.return_value = [_sample_printer()]
    transport = _mock_transport()
    mock_transport_cls.return_value = transport
    mock_decode_status.return_value = _ready_status(tape=TapeWidth.MM_24)
    rendered = Image.new("L", (120, 320), 255)
    mock_render_text.return_value = rendered
    mock_image_to_raster.return_value = [b"\x00" * 70] * 120
    mock_encode_job.return_value = b"job-bytes"

    written = print_text(
        "Hello\nWorld",
        TapeWidth.MM_24,
        font_path="/fonts/test.ttf",
        font_size=32,
        align="left",
        line_spacing=0.25,
        rotate=90,
        margin=4,
        margin_top=8,
        margin_left=10,
        fixed_width=200,
        copies=2,
        threshold=200,
        half_cut=True,
        auto_cut=False,
    )

    mock_render_text.assert_called_once_with(
        "Hello\nWorld",
        TapeWidth.MM_24,
        font_path="/fonts/test.ttf",
        font_size=32,
        align="left",
        line_spacing=0.25,
        rotate=90,
        margin=4,
        margin_top=8,
        margin_bottom=None,
        margin_left=10,
        margin_right=None,
        fixed_width=200,
    )
    mock_image_to_raster.assert_called_once_with(
        rendered,
        TapeWidth.MM_24,
        threshold=200,
        scale=False,
    )
    mock_encode_job.assert_called_once_with(
        TapeWidth.MM_24,
        mock_image_to_raster.return_value,
        auto_cut=False,
        half_cut=True,
    )
    assert written == 200


@patch("brother_ptouch_label.printing.query_status")
@patch("brother_ptouch_label.printing.select_printer")
@patch("brother_ptouch_label.printing.discover")
def test_detect_tape_width_returns_media_width(
    mock_discover,
    mock_select_printer,
    mock_query_status,
):
    """detect_tape_width() reads the loaded tape from printer status."""
    from brother_ptouch_label.printing import detect_tape_width

    printer = _sample_printer()
    mock_discover.return_value = [printer]
    mock_select_printer.return_value = printer
    mock_query_status.return_value = _ready_status(tape=TapeWidth.MM_18)

    assert detect_tape_width() == TapeWidth.MM_18
    mock_select_printer.assert_called_once_with([printer], None)
    mock_query_status.assert_called_once_with(printer)


@patch("brother_ptouch_label.printing.query_status")
@patch("brother_ptouch_label.printing.select_printer")
@patch("brother_ptouch_label.printing.discover")
def test_detect_tape_width_raises_when_no_tape(
    mock_discover,
    mock_select_printer,
    mock_query_status,
):
    """detect_tape_width() raises when the printer reports no tape."""
    from brother_ptouch_label.printing import detect_tape_width

    printer = _sample_printer()
    mock_discover.return_value = [printer]
    mock_select_printer.return_value = printer
    mock_query_status.return_value = PrinterStatus(
        media_width=None,
        media_type=MediaType.LAMINATED,
        errors=(),
        status_type=StatusType.REPLY,
        phase_type=PhaseType.EDITING,
        phase_number=0,
        notification=Notification.NOT_AVAILABLE,
        tape_color=TapeColor.WHITE,
    )

    with pytest.raises(PrintError, match="No tape loaded"):
        detect_tape_width()
