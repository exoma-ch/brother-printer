"""Tests for the brother-label-text CLI."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from brother_printer.protocol.enums import TapeWidth
from brother_printer_text.cli.main import main


@patch("brother_printer_text.cli.main.print_text")
def test_cli_text_success(mock_print_text):
    """CLI prints text labels and reports bytes written."""
    mock_print_text.return_value = 2048
    runner = CliRunner()
    result = runner.invoke(main, ["--text", "Hello", "--tape", "24mm"])
    assert result.exit_code == 0
    assert "2048 bytes" in result.output
    mock_print_text.assert_called_once_with(
        "Hello",
        TapeWidth.MM_24,
        printer=None,
        copies=1,
        font_path=None,
        font_size=None,
        align="center",
        line_spacing=0.0,
        rotate=0,
        margin=0,
        threshold=128,
        auto_cut=True,
        half_cut=False,
    )


@patch("brother_printer_text.cli.main.print_text")
def test_cli_text_unescapes_newlines(mock_print_text):
    """CLI converts literal \\n sequences in --text to newlines."""
    mock_print_text.return_value = 1
    runner = CliRunner()
    result = runner.invoke(main, ["--text", r"Line1\nLine2", "--tape", "24mm"])
    assert result.exit_code == 0
    assert mock_print_text.call_args.args[0] == "Line1\nLine2"
