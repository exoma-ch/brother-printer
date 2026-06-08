"""Tests for the brother-ptouch-driver discover CLI command."""

from unittest.mock import patch

from click.testing import CliRunner

from brother_ptouch_driver.cli.main import main
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


@patch("brother_ptouch_driver.cli.main.discover_printers")
def test_discover_command_lists_printers(mock_discover):
    """discover prints one line per printer with identifier, product, and location."""
    mock_discover.return_value = [_sample_printer()]
    runner = CliRunner()

    result = runner.invoke(main, ["discover"])

    assert result.exit_code == 0
    assert result.output.strip() == "04f9:20c7#000123456789\tPT-E920BT\t1:5"


@patch("brother_ptouch_driver.cli.main.discover_printers")
def test_discover_command_lists_multiple_printers(mock_discover):
    """discover prints each connected printer on its own line."""
    mock_discover.return_value = [
        _sample_printer(serial="000111111111", bus=1, address=3),
        _sample_printer(serial="000222222222", bus=2, address=8),
    ]
    runner = CliRunner()

    result = runner.invoke(main, ["discover"])

    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("04f9:20c7#000111111111")
    assert lines[1].startswith("04f9:20c7#000222222222")


@patch("brother_ptouch_driver.cli.main.discover_printers")
def test_discover_command_exits_nonzero_when_no_printers(mock_discover):
    """discover exits with code 1 when no printers are found."""
    mock_discover.return_value = []
    runner = CliRunner()

    result = runner.invoke(main, ["discover"])

    assert result.exit_code == 1
    assert "No Brother PT-E920BT printers found" in result.output


@patch("brother_ptouch_driver.cli.main.discover_printers")
def test_discover_command_reports_permission_denied(mock_discover):
    """discover surfaces permission errors with udev guidance."""
    from brother_ptouch_driver import PermissionDeniedError

    mock_discover.side_effect = PermissionDeniedError("Access denied")
    runner = CliRunner()

    result = runner.invoke(main, ["discover"])

    assert result.exit_code == 1
    assert "Access denied" in result.output
    assert "udev" in result.output.lower()
