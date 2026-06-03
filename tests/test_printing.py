"""Tests for the print_image() library orchestrator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from brother_printer.protocol.decoder import PrinterStatus
from brother_printer.protocol.enums import (
    MediaType,
    Notification,
    PhaseType,
    StatusType,
    TapeColor,
    TapeWidth,
)
from brother_printer.transport.base import PrinterInfo
from brother_printer.transport.errors import DeviceNotFoundError


def _sample_printer(
    *, serial: str = "000123456789", bus: int = 1, address: int = 5
) -> PrinterInfo:
    return PrinterInfo(
        vendor_id=0x04F9,
        product_id=0x20C7,
        serial=serial,
        product="PT-E920BT",
        bus=bus,
        address=address,
    )


def _ready_status(
    *,
    tape: TapeWidth = TapeWidth.MM_24,
    media_type: MediaType = MediaType.LAMINATED,
) -> PrinterStatus:
    return PrinterStatus(
        media_width=tape,
        media_type=media_type,
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


@patch("brother_printer.printing.encode_job")
@patch("brother_printer.printing.image_to_raster")
@patch("brother_printer.printing.decode_status")
@patch("brother_printer.printing.status_request", return_value=b"\x1biS")
@patch("brother_printer.printing.UsbTransport")
@patch("brother_printer.printing.discover")
def test_print_image_passes_half_cut(
    mock_discover,
    mock_transport_cls,
    mock_status_request,
    mock_decode_status,
    mock_image_to_raster,
    mock_encode_job,
):
    """print_image() forwards half_cut to encode_job()."""
    from brother_printer import print_image

    mock_discover.return_value = [_sample_printer()]
    transport = _mock_transport()
    mock_transport_cls.return_value = transport
    mock_decode_status.return_value = _ready_status(tape=TapeWidth.MM_24)
    mock_image_to_raster.return_value = [b"\x00" * 70] * 60
    mock_encode_job.return_value = b"job-bytes"

    image = Image.new("L", (80, 80), 255)
    print_image(image, TapeWidth.MM_24, half_cut=True, auto_cut=True)

    mock_encode_job.assert_called_once_with(
        TapeWidth.MM_24,
        mock_image_to_raster.return_value,
        auto_cut=True,
        half_cut=True,
    )


@patch("brother_printer.printing.encode_strip_job")
@patch("brother_printer.printing.image_to_raster")
@patch("brother_printer.printing.decode_status")
@patch("brother_printer.printing.status_request", return_value=b"\x1biS")
@patch("brother_printer.printing.UsbTransport")
@patch("brother_printer.printing.discover")
def test_print_strip_writes_one_job_for_multiple_images(
    mock_discover,
    mock_transport_cls,
    mock_status_request,
    mock_decode_status,
    mock_image_to_raster,
    mock_encode_strip_job,
):
    """print_strip() rasterizes each image and sends one encoded strip job."""
    from brother_printer import print_strip

    mock_discover.return_value = [_sample_printer()]
    transport = _mock_transport()
    mock_transport_cls.return_value = transport
    mock_decode_status.return_value = _ready_status(tape=TapeWidth.MM_24)
    mock_image_to_raster.side_effect = [
        [b"\x01" * 70] * 2,
        [b"\x02" * 70] * 3,
    ]
    mock_encode_strip_job.return_value = b"strip-bytes"

    images = [Image.new("L", (80, 80), 255), Image.new("L", (60, 60), 0)]
    written = print_strip(
        images,
        TapeWidth.MM_24,
        half_cut=True,
        auto_cut=True,
        threshold=100,
        rotate=90,
        margin=4,
    )

    assert mock_image_to_raster.call_count == 2
    mock_encode_strip_job.assert_called_once_with(
        TapeWidth.MM_24,
        [[b"\x01" * 70] * 2, [b"\x02" * 70] * 3],
        auto_cut=True,
        half_cut=True,
    )
    assert transport.write.call_count == 2  # status + strip job
    assert written == 100


@patch("brother_printer.printing.encode_strip_job")
@patch("brother_printer.printing.image_to_raster")
@patch("brother_printer.printing.decode_status")
@patch("brother_printer.printing.status_request", return_value=b"\x1biS")
@patch("brother_printer.printing.UsbTransport")
@patch("brother_printer.printing.discover")
def test_print_strip_expands_copies_into_pages(
    mock_discover,
    mock_transport_cls,
    mock_status_request,
    mock_decode_status,
    mock_image_to_raster,
    mock_encode_strip_job,
):
    """print_strip() repeats raster pages when copies > 1."""
    from brother_printer import print_strip

    mock_discover.return_value = [_sample_printer()]
    transport = _mock_transport()
    mock_transport_cls.return_value = transport
    mock_decode_status.return_value = _ready_status(tape=TapeWidth.MM_24)
    raster = [b"\x00" * 70] * 2
    mock_image_to_raster.return_value = raster
    mock_encode_strip_job.return_value = b"strip-bytes"

    image = Image.new("L", (80, 80), 255)
    print_strip([image], TapeWidth.MM_24, copies=3)

    mock_encode_strip_job.assert_called_once_with(
        TapeWidth.MM_24,
        [raster, raster, raster],
        auto_cut=True,
        half_cut=False,
    )


@patch("brother_printer.printing.encode_job")
@patch("brother_printer.printing.image_to_raster")
@patch("brother_printer.printing.decode_status")
@patch("brother_printer.printing.status_request", return_value=b"\x1biS")
@patch("brother_printer.printing.UsbTransport")
@patch("brother_printer.printing.discover")
def test_print_image_writes_job_for_each_copy(
    mock_discover,
    mock_transport_cls,
    mock_status_request,
    mock_decode_status,
    mock_image_to_raster,
    mock_encode_job,
):
    """print_image() sends the encoded job once per copy and returns total bytes."""
    from brother_printer import print_image

    printer = _sample_printer()
    mock_discover.return_value = [printer]
    transport = _mock_transport()
    mock_transport_cls.return_value = transport
    mock_decode_status.return_value = _ready_status(tape=TapeWidth.MM_24)
    mock_image_to_raster.return_value = [b"\x00" * 70] * 60
    mock_encode_job.return_value = b"job-bytes"

    image = Image.new("L", (80, 80), 255)
    written = print_image(
        image,
        TapeWidth.MM_24,
        copies=2,
        threshold=100,
        rotate=90,
        margin=4,
        auto_cut=False,
    )

    mock_transport_cls.assert_called_once_with(printer)
    mock_status_request.assert_called_once_with()
    transport.write.assert_any_call(b"\x1biS")
    mock_image_to_raster.assert_called_once_with(
        image,
        TapeWidth.MM_24,
        threshold=100,
        rotate=90,
        margin=4,
        allow_distortion=False,
    )
    mock_encode_job.assert_called_once_with(
        TapeWidth.MM_24,
        mock_image_to_raster.return_value,
        auto_cut=False,
        half_cut=False,
    )
    assert transport.write.call_count == 3  # status + 2 copies
    assert written == 200


@patch("brother_printer.printing.decode_status")
@patch("brother_printer.printing.UsbTransport")
@patch("brother_printer.printing.discover")
def test_print_image_selects_printer_by_identifier(
    mock_discover,
    mock_transport_cls,
    mock_decode_status,
):
    """print_image() opens the printer matching the identifier when provided."""
    from brother_printer import print_image

    first = _sample_printer(serial="000111111111")
    second = _sample_printer(serial="000222222222")
    mock_discover.return_value = [first, second]
    transport = _mock_transport()
    mock_transport_cls.return_value = transport
    mock_decode_status.return_value = _ready_status(tape=TapeWidth.MM_24)

    with patch(
        "brother_printer.printing.image_to_raster", return_value=[b"\x00" * 70] * 60
    ):
        with patch("brother_printer.printing.encode_job", return_value=b"job"):
            print_image(
                Image.new("L", (80, 80), 255),
                TapeWidth.MM_24,
                printer=second.identifier,
            )

    mock_transport_cls.assert_called_once_with(second)


@patch("brother_printer.printing.discover")
def test_print_image_raises_when_no_printer_found(mock_discover):
    """print_image() raises DeviceNotFoundError when discover() returns nothing."""
    from brother_printer import print_image

    mock_discover.return_value = []

    with pytest.raises(
        DeviceNotFoundError, match="No Brother PT-E920BT printers found"
    ):
        print_image(Image.new("L", (1, 1), 255), TapeWidth.MM_24)


@patch("brother_printer.printing.discover")
def test_print_image_raises_when_printer_identifier_not_found(mock_discover):
    """print_image() raises DeviceNotFoundError when the identifier is unknown."""
    from brother_printer import print_image

    mock_discover.return_value = [_sample_printer()]

    with pytest.raises(DeviceNotFoundError, match="No printer found for identifier"):
        print_image(
            Image.new("L", (1, 1), 255),
            TapeWidth.MM_24,
            printer="04f9:20c7#missing",
        )


@patch("brother_printer.printing.decode_status")
@patch("brother_printer.printing.UsbTransport")
@patch("brother_printer.printing.discover")
def test_print_image_raises_tape_mismatch(
    mock_discover,
    mock_transport_cls,
    mock_decode_status,
):
    """print_image() refuses to print when requested tape does not match loaded tape."""
    from brother_printer import TapeMismatchError, print_image

    mock_discover.return_value = [_sample_printer()]
    mock_transport_cls.return_value = _mock_transport()
    mock_decode_status.return_value = _ready_status(tape=TapeWidth.MM_12)

    with pytest.raises(TapeMismatchError, match="12"):
        print_image(Image.new("L", (1, 1), 255), TapeWidth.MM_24)


@patch("brother_printer.printing.decode_status")
@patch("brother_printer.printing.UsbTransport")
@patch("brother_printer.printing.discover")
def test_print_image_raises_when_no_tape_loaded(
    mock_discover,
    mock_transport_cls,
    mock_decode_status,
):
    """print_image() raises PrinterNotReadyError when no tape width is reported."""
    from brother_printer import PrinterNotReadyError, print_image

    mock_discover.return_value = [_sample_printer()]
    mock_transport_cls.return_value = _mock_transport()
    mock_decode_status.return_value = _ready_status(tape=None)  # type: ignore[arg-type]

    with pytest.raises(PrinterNotReadyError, match="No tape loaded"):
        print_image(Image.new("L", (1, 1), 255), TapeWidth.MM_24)


@patch("brother_printer.printing.decode_status")
@patch("brother_printer.printing.UsbTransport")
@patch("brother_printer.printing.discover")
def test_print_image_raises_when_printer_reports_errors(
    mock_discover,
    mock_transport_cls,
    mock_decode_status,
):
    """print_image() raises PrinterNotReadyError when the status reply lists errors."""
    from brother_printer import PrinterNotReadyError, print_image

    mock_discover.return_value = [_sample_printer()]
    mock_transport_cls.return_value = _mock_transport()
    status = _ready_status(tape=TapeWidth.MM_24)
    mock_decode_status.return_value = PrinterStatus(
        media_width=status.media_width,
        media_type=status.media_type,
        errors=("Cover open",),
        status_type=status.status_type,
        phase_type=status.phase_type,
        phase_number=status.phase_number,
        notification=status.notification,
        tape_color=status.tape_color,
    )

    with pytest.raises(PrinterNotReadyError, match="Cover open"):
        print_image(Image.new("L", (1, 1), 255), TapeWidth.MM_24)


def test_select_printer_returns_first_when_identifier_none():
    """select_printer() picks the first printer when no identifier is given."""
    from brother_printer import select_printer

    first = _sample_printer(serial="000111111111")
    second = _sample_printer(serial="000222222222")
    assert select_printer([first, second], None) is first


def test_select_printer_returns_matching_identifier():
    """select_printer() returns the printer with the given identifier."""
    from brother_printer import select_printer

    first = _sample_printer(serial="000111111111")
    second = _sample_printer(serial="000222222222")
    assert select_printer([first, second], second.identifier) is second


def test_select_printer_raises_when_list_empty():
    """select_printer() raises DeviceNotFoundError for an empty printer list."""
    from brother_printer import select_printer

    with pytest.raises(
        DeviceNotFoundError, match="No Brother PT-E920BT printers found"
    ):
        select_printer([], None)


@patch("brother_printer.printing.decode_status")
@patch("brother_printer.printing.UsbTransport")
def test_query_status_reads_status_reply(mock_transport_cls, mock_decode_status):
    """query_status() sends status_request and decodes the 32-byte reply."""
    from brother_printer import query_status

    printer = _sample_printer()
    transport = _mock_transport()
    mock_transport_cls.return_value = transport
    status_bytes = b"\x80\x20" + b"\x00" * 30
    transport.read_exact.return_value = status_bytes
    expected = _ready_status(tape=TapeWidth.MM_24)
    mock_decode_status.return_value = expected

    status = query_status(printer)

    mock_transport_cls.assert_called_once_with(printer)
    transport.write.assert_called_once()
    transport.read_exact.assert_called_once_with(32, timeout_ms=5000)
    mock_decode_status.assert_called_once_with(status_bytes)
    assert status is expected


@patch("brother_printer.printing.decode_status")
@patch("brother_printer.printing.UsbTransport")
@patch("brother_printer.printing.discover")
def test_print_image_raises_half_cut_on_non_laminated(
    mock_discover,
    mock_transport_cls,
    mock_decode_status,
):
    """print_image() rejects half-cut when loaded tape is not laminated."""
    from brother_printer import HalfCutNotSupportedError, print_image

    mock_discover.return_value = [_sample_printer()]
    mock_transport_cls.return_value = _mock_transport()
    mock_decode_status.return_value = _ready_status(
        tape=TapeWidth.MM_24,
        media_type=MediaType.NON_LAMINATED,
    )

    with pytest.raises(HalfCutNotSupportedError, match="laminated"):
        print_image(Image.new("L", (1, 1), 255), TapeWidth.MM_24, half_cut=True)


@patch("brother_printer.printing.decode_status")
@patch("brother_printer.printing.UsbTransport")
@patch("brother_printer.printing.discover")
def test_print_strip_raises_half_cut_on_non_laminated(
    mock_discover,
    mock_transport_cls,
    mock_decode_status,
):
    """print_strip() rejects half-cut when loaded tape is not laminated."""
    from brother_printer import HalfCutNotSupportedError, print_strip

    mock_discover.return_value = [_sample_printer()]
    mock_transport_cls.return_value = _mock_transport()
    mock_decode_status.return_value = _ready_status(
        tape=TapeWidth.MM_36,
        media_type=MediaType.NON_LAMINATED,
    )

    with pytest.raises(HalfCutNotSupportedError, match="laminated"):
        print_strip(
            [Image.new("L", (1, 1), 255), Image.new("L", (1, 1), 255)],
            TapeWidth.MM_36,
            half_cut=True,
        )
