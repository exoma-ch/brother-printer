"""Tests for the brother-printer print CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from PIL import Image

from brother_printer.cli.main import main
from brother_printer.protocol.enums import TapeWidth


def _write_test_image(path: Path) -> None:
    Image.new("L", (80, 80), 255).save(path)


@patch("brother_printer.cli.main.print_image")
def test_print_command_success(mock_print_image):
    """print reports bytes written on success."""
    mock_print_image.return_value = 2048
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"))
        result = runner.invoke(main, ["print", "label.png", "--tape", "24mm"])

    assert result.exit_code == 0
    assert "2048 bytes" in result.output
    mock_print_image.assert_called_once()
    _, kwargs = mock_print_image.call_args
    assert kwargs["copies"] == 1
    assert kwargs["threshold"] == 128
    assert kwargs["rotate"] == 0
    assert kwargs["margin"] == 0
    assert kwargs["auto_cut"] is True
    assert kwargs["printer"] is None


@patch("brother_printer.cli.main.print_image")
def test_print_command_passes_options(mock_print_image):
    """print forwards CLI options to print_image()."""
    mock_print_image.return_value = 100
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"))
        result = runner.invoke(
            main,
            [
                "print",
                "label.png",
                "--tape",
                "12mm",
                "--no-cut",
                "--copies",
                "3",
                "--threshold",
                "200",
                "--rotate",
                "90",
                "--margin",
                "5",
                "--printer",
                "04f9:20c7#000123456789",
            ],
        )

    assert result.exit_code == 0
    args, kwargs = mock_print_image.call_args
    assert args[1] == TapeWidth.MM_12
    assert kwargs == {
        "printer": "04f9:20c7#000123456789",
        "copies": 3,
        "threshold": 200,
        "rotate": 90,
        "margin": 5,
        "auto_cut": False,
    }


@pytest.mark.parametrize(
    ("tape_arg", "expected"),
    [
        ("3.5mm", TapeWidth.MM_3_5),
        ("6mm", TapeWidth.MM_6),
        ("9mm", TapeWidth.MM_9),
        ("12mm", TapeWidth.MM_12),
        ("18mm", TapeWidth.MM_18),
        ("24mm", TapeWidth.MM_24),
        ("36mm", TapeWidth.MM_36),
    ],
)
@patch("brother_printer.cli.main.print_image")
def test_print_command_maps_tape_choices(mock_print_image, tape_arg, expected):
    """print maps --tape choices to TapeWidth enum members."""
    mock_print_image.return_value = 1
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"))
        result = runner.invoke(main, ["print", "label.png", "--tape", tape_arg])

    assert result.exit_code == 0
    assert mock_print_image.call_args.args[1] == expected


@patch("brother_printer.cli.main.print_image")
def test_print_command_reports_tape_mismatch(mock_print_image):
    """print surfaces tape mismatch errors on stderr and exits 1."""
    from brother_printer import TapeMismatchError

    mock_print_image.side_effect = TapeMismatchError("Loaded tape is 12 mm")
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"))
        result = runner.invoke(main, ["print", "label.png", "--tape", "24mm"])

    assert result.exit_code == 1
    assert "12 mm" in result.output


@patch("brother_printer.cli.main.print_image")
def test_print_command_reports_printer_not_ready(mock_print_image):
    """print surfaces printer-not-ready errors on stderr and exits 1."""
    from brother_printer import PrinterNotReadyError

    mock_print_image.side_effect = PrinterNotReadyError("Cover open")
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"))
        result = runner.invoke(main, ["print", "label.png", "--tape", "24mm"])

    assert result.exit_code == 1
    assert "Cover open" in result.output


@patch("brother_printer.cli.main.print_image")
def test_print_command_reports_transport_error(mock_print_image):
    """print surfaces transport errors on stderr and exits 1."""
    from brother_printer.transport.errors import PermissionDeniedError

    mock_print_image.side_effect = PermissionDeniedError("Access denied")
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"))
        result = runner.invoke(main, ["print", "label.png", "--tape", "24mm"])

    assert result.exit_code == 1
    assert "Access denied" in result.output


@patch("brother_printer.cli.main.print_image")
def test_print_command_reports_imaging_error(mock_print_image):
    """print surfaces imaging errors on stderr and exits 1."""
    from brother_printer.imaging.errors import ImageScalingError

    mock_print_image.side_effect = ImageScalingError("QR modules would distort")
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"))
        result = runner.invoke(main, ["print", "label.png", "--tape", "24mm"])

    assert result.exit_code == 1
    assert "QR modules would distort" in result.output
