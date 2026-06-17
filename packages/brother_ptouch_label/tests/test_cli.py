"""Tests for the brother-ptouch-label CLI."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
from PIL import Image

from brother_ptouch_driver.protocol.enums import TapeWidth
from brother_ptouch_label.cli.main import main


@patch("brother_ptouch_label.cli.main.print_text")
def test_cli_text_success(mock_print_text):
    """CLI prints text labels and reports bytes written."""
    mock_print_text.return_value = 2048
    runner = CliRunner()
    result = runner.invoke(main, ["Hello", "--tape", "24mm"])
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
        margin_top=None,
        margin_bottom=None,
        margin_left=None,
        margin_right=None,
        fixed_width=None,
        replicate=1,
        threshold=128,
        auto_cut=True,
        half_cut=False,
    )


@patch("brother_ptouch_label.cli.main.print_text")
def test_cli_text_unescapes_newlines(mock_print_text):
    """CLI converts literal \\n sequences in text to newlines."""
    mock_print_text.return_value = 1
    runner = CliRunner()
    result = runner.invoke(main, [r"Line1\nLine2", "--tape", "24mm"])
    assert result.exit_code == 0
    assert mock_print_text.call_args.args[0] == "Line1\nLine2"


@patch("brother_ptouch_label.cli.main.print_text")
def test_cli_rotate_flag_passes_90(mock_print_text):
    """--rotate maps to rotate=90 for print_text."""
    mock_print_text.return_value = 1
    runner = CliRunner()
    result = runner.invoke(main, ["Hi", "--tape", "24mm", "--rotate"])
    assert result.exit_code == 0
    assert mock_print_text.call_args.kwargs["rotate"] == 90


@patch("brother_ptouch_label.cli.main.detect_tape_width")
@patch("brother_ptouch_label.cli.main.print_text")
def test_cli_auto_detects_tape(mock_print_text, mock_detect):
    """CLI reads tape width from the printer when --tape is omitted."""
    mock_detect.return_value = TapeWidth.MM_12
    mock_print_text.return_value = 1
    runner = CliRunner()
    result = runner.invoke(main, ["Hi"])
    assert result.exit_code == 0
    mock_detect.assert_called_once_with(printer=None)
    assert mock_print_text.call_args.args[1] == TapeWidth.MM_12


@patch("brother_ptouch_label.cli.main.render_text")
@patch("brother_ptouch_label.cli.main.print_text")
def test_cli_output_writes_png(mock_print_text, mock_render_text, tmp_path: Path):
    """--output renders PNG without calling print_text."""
    image = Image.new("L", (100, 320), 255)
    mock_render_text.return_value = image
    out = tmp_path / "label.png"
    runner = CliRunner()
    result = runner.invoke(main, ["Hi", "--tape", "24mm", "-o", str(out)])
    assert result.exit_code == 0
    assert "Wrote" in result.output
    mock_print_text.assert_not_called()
    mock_render_text.assert_called_once()
    assert out.is_file()


@patch("brother_ptouch_label.cli.main.print_text")
def test_cli_replicate_option_forwarded(mock_print_text):
    """--replicate is forwarded to print_text."""
    mock_print_text.return_value = 1
    runner = CliRunner()
    result = runner.invoke(main, ["Hi", "--tape", "24mm", "--replicate", "3"])
    assert result.exit_code == 0
    assert mock_print_text.call_args.kwargs["replicate"] == 3


@patch("brother_ptouch_label.cli.main.print_text")
def test_cli_repeat_alias_forwarded(mock_print_text):
    """The --repeat alias maps to the same replicate option."""
    mock_print_text.return_value = 1
    runner = CliRunner()
    result = runner.invoke(main, ["Hi", "--tape", "24mm", "--repeat", "2"])
    assert result.exit_code == 0
    assert mock_print_text.call_args.kwargs["replicate"] == 2


@patch("brother_ptouch_label.cli.main.print_text")
def test_cli_margin_and_width_options(mock_print_text):
    """CLI forwards per-edge margins and fixed width."""
    mock_print_text.return_value = 1
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "Hi",
            "--tape",
            "24mm",
            "--margin",
            "2",
            "--margin-left",
            "10",
            "--width",
            "400",
        ],
    )
    assert result.exit_code == 0
    kwargs = mock_print_text.call_args.kwargs
    assert kwargs["margin"] == 2
    assert kwargs["margin_left"] == 10
    assert kwargs["fixed_width"] == 400
