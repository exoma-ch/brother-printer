"""Opt-in hardware status tests for a real PT-E920BT.

Run with::

    just test-hardware packages/brother_printer/tests/hardware/test_status.py

Requires USB passthrough and udev permissions (see docs/install/linux-usb.md).
Non-destructive: no tape is consumed.
"""

from __future__ import annotations

from click.testing import CliRunner

from brother_printer import discover_printers, query_status, select_printer
from brother_printer.cli.main import main
from brother_printer.protocol import (
    STATUS_REPLY_SIZE,
    StatusType,
    TapeWidth,
    decode_status,
    status_request,
)
from brother_printer.transport import UsbTransport, discover

from tests.hardware.conftest import (  # noqa: F401
    HARDWARE_PYTESTMARK as pytestmark,
    PRINTER_REQUIRED_MSG,
    STATUS_READ_TIMEOUT_MS,
)

_STATUS_LABELS = ("Tape:", "Color:", "Media:", "Phase:", "Status:")


def _require_printers():
    printers = discover_printers()
    assert printers, PRINTER_REQUIRED_MSG
    return printers


def test_status_request_round_trip():
    """status_request() over USB returns a decodable 32-byte status reply."""
    printers = discover()
    assert printers, PRINTER_REQUIRED_MSG

    with UsbTransport(printers[0]) as transport:
        transport.write(status_request())
        reply = transport.read_exact(
            STATUS_REPLY_SIZE, timeout_ms=STATUS_READ_TIMEOUT_MS
        )

    status = decode_status(reply)
    assert status.status_type == StatusType.REPLY
    assert status.media_width is None or isinstance(status.media_width, TapeWidth)


def test_query_status_library_api():
    """query_status() over USB returns a decodable status reply."""
    printers = _require_printers()
    status = query_status(select_printer(printers, None))

    assert status.status_type == StatusType.REPLY
    assert status.media_width is None or isinstance(status.media_width, TapeWidth)


def test_status_cli_command():
    """brother-printer status renders a human-readable status table."""
    _require_printers()
    runner = CliRunner()

    result = runner.invoke(main, ["status"])

    assert result.exit_code in (0, 1)
    for label in _STATUS_LABELS:
        assert label in result.output

    status_line = next(
        line
        for line in result.output.splitlines()
        if line.strip().startswith("Status:")
    )
    status_value = status_line.split("Status:", 1)[1].strip()
    if result.exit_code == 0:
        assert status_value == "Ready"
    else:
        assert status_value != "Ready"


def test_discover_status_cli_flag():
    """brother-printer discover --status renders status tables per printer."""
    _require_printers()
    runner = CliRunner()

    result = runner.invoke(main, ["discover", "--status"])

    assert result.exit_code in (0, 1)
    assert "Tape:" in result.output
    assert "Status:" in result.output
    assert "\t" not in result.output.split("Tape:")[0]
