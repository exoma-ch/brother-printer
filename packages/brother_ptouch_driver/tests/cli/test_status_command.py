"""Tests for the brother-ptouch-driver status CLI command."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from brother_ptouch_driver.cli.main import main
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


def _ready_status(*, tape: TapeWidth = TapeWidth.MM_12) -> PrinterStatus:
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


@patch("brother_ptouch_driver.cli.main.query_status")
@patch("brother_ptouch_driver.cli.main.select_printer")
@patch("brother_ptouch_driver.cli.main.discover_printers")
def test_status_command_shows_ready_printer(
    mock_discover, mock_select, mock_query_status
):
    """status prints a human-readable table and exits 0 when ready."""
    printer = _sample_printer()
    mock_discover.return_value = [printer]
    mock_select.return_value = printer
    mock_query_status.return_value = _ready_status()
    runner = CliRunner()

    result = runner.invoke(main, ["status"])

    assert result.exit_code == 0
    assert "PT-E920BT" in result.output
    assert "04f9:20c7#000123456789" in result.output
    assert "Tape:       12 mm" in result.output
    assert "Color:      White" in result.output
    assert "Media:      Laminated" in result.output
    assert "Phase:      Idle" in result.output
    assert "Status:     Ready" in result.output


@patch("brother_ptouch_driver.cli.main.query_status")
@patch("brother_ptouch_driver.cli.main.select_printer")
@patch("brother_ptouch_driver.cli.main.discover_printers")
def test_status_command_passes_printer_identifier(
    mock_discover, mock_select, mock_query_status
):
    """status forwards -p/--printer to select_printer()."""
    printers = [
        _sample_printer(serial="000111111111"),
        _sample_printer(serial="000222222222"),
    ]
    mock_discover.return_value = printers
    mock_select.return_value = printers[1]
    mock_query_status.return_value = _ready_status()
    runner = CliRunner()

    result = runner.invoke(main, ["status", "-p", "04f9:20c7#000222222222"])

    assert result.exit_code == 0
    mock_select.assert_called_once_with(printers, "04f9:20c7#000222222222")


@patch("brother_ptouch_driver.cli.main.query_status")
@patch("brother_ptouch_driver.cli.main.select_printer")
@patch("brother_ptouch_driver.cli.main.discover_printers")
def test_status_command_exits_nonzero_on_printer_errors(
    mock_discover, mock_select, mock_query_status
):
    """status exits 1 when the status reply lists errors."""
    printer = _sample_printer()
    mock_discover.return_value = [printer]
    mock_select.return_value = printer
    ready = _ready_status()
    mock_query_status.return_value = PrinterStatus(
        media_width=ready.media_width,
        media_type=ready.media_type,
        errors=("Cover open",),
        status_type=ready.status_type,
        phase_type=ready.phase_type,
        phase_number=ready.phase_number,
        notification=ready.notification,
        tape_color=ready.tape_color,
    )
    runner = CliRunner()

    result = runner.invoke(main, ["status"])

    assert result.exit_code == 1
    assert "Cover open" in result.output


@patch("brother_ptouch_driver.cli.main.discover_printers")
def test_status_command_reports_device_not_found(mock_discover):
    """status surfaces DeviceNotFoundError and exits 1."""
    mock_discover.return_value = []
    runner = CliRunner()

    result = runner.invoke(main, ["status"])

    assert result.exit_code == 1
    assert "No Brother PT-E920BT printers found" in result.output


@patch("brother_ptouch_driver.cli.main.discover_printers")
def test_status_command_reports_transport_error(mock_discover):
    """status surfaces transport errors and exits 1."""
    from brother_ptouch_driver import PermissionDeniedError

    mock_discover.side_effect = PermissionDeniedError("Access denied")
    runner = CliRunner()

    result = runner.invoke(main, ["status"])

    assert result.exit_code == 1
    assert "Access denied" in result.output
