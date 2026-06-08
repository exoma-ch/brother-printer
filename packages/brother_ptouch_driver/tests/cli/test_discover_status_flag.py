"""Tests for brother-ptouch-driver discover --status."""

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


def _ready_status() -> PrinterStatus:
    return PrinterStatus(
        media_width=TapeWidth.MM_24,
        media_type=MediaType.LAMINATED,
        errors=(),
        status_type=StatusType.REPLY,
        phase_type=PhaseType.EDITING,
        phase_number=0,
        notification=Notification.NOT_AVAILABLE,
        tape_color=TapeColor.WHITE,
    )


@patch("brother_ptouch_driver.cli.main.query_status")
@patch("brother_ptouch_driver.cli.main.discover_printers")
def test_discover_status_flag_shows_status_table(mock_discover, mock_query_status):
    """discover -s renders status tables instead of tab-separated lines."""
    printer = _sample_printer()
    mock_discover.return_value = [printer]
    mock_query_status.return_value = _ready_status()
    runner = CliRunner()

    result = runner.invoke(main, ["discover", "--status"])

    assert result.exit_code == 0
    assert "Tape:       24 mm" in result.output
    assert "Status:     Ready" in result.output
    assert "\t" not in result.output.split("Tape:")[0]


@patch("brother_ptouch_driver.cli.main.query_status")
@patch("brother_ptouch_driver.cli.main.discover_printers")
def test_discover_status_flag_degrades_on_per_printer_failure(
    mock_discover, mock_query_status
):
    """discover -s continues after a per-printer status query failure."""
    from brother_ptouch_driver import DeviceBusyError

    first = _sample_printer(serial="000111111111")
    second = _sample_printer(serial="000222222222")
    mock_discover.return_value = [first, second]
    mock_query_status.side_effect = [
        DeviceBusyError("Device busy"),
        _ready_status(),
    ]
    runner = CliRunner()

    result = runner.invoke(main, ["discover", "-s"])

    assert result.exit_code == 1
    assert "000111111111" in result.output
    assert "Device busy" in result.output
    assert "000222222222" in result.output
    assert "Status:     Ready" in result.output


@patch("brother_ptouch_driver.cli.main.query_status")
@patch("brother_ptouch_driver.cli.main.discover_printers")
def test_discover_without_status_flag_unchanged(mock_discover, mock_query_status):
    """Plain discover does not call query_status."""
    mock_discover.return_value = [_sample_printer()]
    runner = CliRunner()

    result = runner.invoke(main, ["discover"])

    assert result.exit_code == 0
    assert result.output.strip() == "04f9:20c7#000123456789\tPT-E920BT\t1:5"
    mock_query_status.assert_not_called()
