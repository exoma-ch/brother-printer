"""Opt-in hardware test for status query and CLI status commands.

These tests query live printer status over USB and are skipped unless
``BROTHER_PRINTER_HARDWARE=1`` is set. Run them with::

    just test-hardware tests/hardware/test_status_hardware.py

They require USB passthrough into the devcontainer (see
docs/install/linux-usb.md) and the libusb backend. Non-destructive:
no tape is consumed.
"""

from __future__ import annotations

import os

import pytest
from click.testing import CliRunner

from brother_printer import discover_printers, query_status, select_printer
from brother_printer.cli.main import main
from brother_printer.protocol.enums import StatusType, TapeWidth

_HARDWARE_ENABLED = os.environ.get("BROTHER_PRINTER_HARDWARE") == "1"

_PRINTER_REQUIRED_MSG = (
    "No PT-E920BT found. Confirm the printer is connected and powered, "
    "USB passthrough is configured, and udev permissions are set "
    "(see docs/install/linux-usb.md)."
)

_STATUS_LABELS = ("Tape:", "Color:", "Media:", "Phase:", "Status:")

pytestmark = [
    pytest.mark.hardware,
    pytest.mark.skipif(
        not _HARDWARE_ENABLED,
        reason="set BROTHER_PRINTER_HARDWARE=1 to run hardware status tests",
    ),
]


def _require_printers():
    printers = discover_printers()
    assert printers, _PRINTER_REQUIRED_MSG
    return printers


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
