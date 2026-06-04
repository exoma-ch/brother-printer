"""Tests for the brother-ptouch-driver print CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from PIL import Image

from brother_ptouch_driver.cli.main import main
from brother_ptouch_driver.protocol.enums import TapeWidth


def _write_test_image(path: Path, *, height: int | None = None) -> None:
    h = height if height is not None else TapeWidth.MM_24.print_area_pins
    Image.new("L", (80, h), 255).save(path)


@patch("brother_ptouch_driver.cli.main.print_image")
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
    assert kwargs["auto_cut"] is True
    assert kwargs["half_cut"] is False
    assert kwargs["scale"] is False
    assert kwargs["printer"] is None


@patch("brother_ptouch_driver.cli.main.print_strip")
def test_print_command_multiple_paths_use_strip(mock_print_strip):
    """print uses print_strip() when multiple image paths are provided."""
    mock_print_strip.return_value = 4096
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("a.png"))
        _write_test_image(Path("b.png"))
        result = runner.invoke(main, ["print", "a.png", "b.png", "--tape", "24mm"])

    assert result.exit_code == 0
    mock_print_strip.assert_called_once()
    args, kwargs = mock_print_strip.call_args
    assert args[1] == TapeWidth.MM_24
    assert len(args[0]) == 2
    assert kwargs["copies"] == 1
    assert kwargs["half_cut"] is False


@patch("brother_ptouch_driver.cli.main.print_strip")
def test_print_command_strip_flag_chains_copies(mock_print_strip):
    """print uses print_strip() for a single image when --strip is set."""
    mock_print_strip.return_value = 3000
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"))
        result = runner.invoke(
            main,
            ["print", "label.png", "--tape", "24mm", "--strip", "--copies", "3"],
        )

    assert result.exit_code == 0
    mock_print_strip.assert_called_once()
    _, kwargs = mock_print_strip.call_args
    assert kwargs["copies"] == 3


@patch("brother_ptouch_driver.cli.main.print_strip")
def test_print_command_csv_uses_strip(mock_print_strip):
    """print uses print_strip() when --csv is provided."""
    mock_print_strip.return_value = 5000
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("a.png"))
        _write_test_image(Path("b.png"))
        Path("jobs.csv").write_text(
            "image,copies\na.png,2\nb.png,1\n",
            encoding="utf-8",
        )
        result = runner.invoke(
            main,
            ["print", "--tape", "24mm", "--csv", "jobs.csv", "--half-cut"],
        )

    assert result.exit_code == 0
    mock_print_strip.assert_called_once()
    args, kwargs = mock_print_strip.call_args
    assert len(args[0]) == 3
    assert kwargs["copies"] == 1
    assert kwargs["half_cut"] is True


@patch("brother_ptouch_driver.cli.main.print_image")
def test_print_command_rejects_paths_and_csv_together(mock_print_image):
    """print exits 2 when both paths and --csv are provided."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"))
        Path("jobs.csv").write_text("image\nlabel.png\n", encoding="utf-8")
        result = runner.invoke(
            main,
            ["print", "label.png", "--tape", "24mm", "--csv", "jobs.csv"],
        )

    assert result.exit_code == 2
    assert "exactly one" in result.output
    mock_print_image.assert_not_called()


def test_print_command_requires_input_source():
    """print exits 2 when no image path or CSV is provided."""
    runner = CliRunner()
    result = runner.invoke(main, ["print", "--tape", "24mm"])
    assert result.exit_code == 2
    assert "at least one" in result.output


@patch("brother_ptouch_driver.cli.main.print_image")
def test_print_command_passes_scale_flag(mock_print_image):
    """print forwards --scale to print_image()."""
    mock_print_image.return_value = 100
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"), height=80)
        result = runner.invoke(
            main,
            ["print", "label.png", "--tape", "24mm", "--scale"],
        )

    assert result.exit_code == 0
    assert mock_print_image.call_args.kwargs["scale"] is True


@patch("brother_ptouch_driver.cli.main.print_image")
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
        "auto_cut": False,
        "half_cut": False,
        "scale": False,
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
@patch("brother_ptouch_driver.cli.main.print_image")
def test_print_command_maps_tape_choices(mock_print_image, tape_arg, expected):
    """print maps --tape choices to TapeWidth enum members."""
    mock_print_image.return_value = 1
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"))
        result = runner.invoke(main, ["print", "label.png", "--tape", tape_arg])

    assert result.exit_code == 0
    assert mock_print_image.call_args.args[1] == expected


@patch("brother_ptouch_driver.cli.main.print_image")
def test_print_command_reports_tape_mismatch(mock_print_image):
    """print surfaces tape mismatch errors on stderr and exits 1."""
    from brother_ptouch_driver import TapeMismatchError

    mock_print_image.side_effect = TapeMismatchError("Loaded tape is 12 mm")
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"))
        result = runner.invoke(main, ["print", "label.png", "--tape", "24mm"])

    assert result.exit_code == 1
    assert "12 mm" in result.output


@patch("brother_ptouch_driver.cli.main.print_image")
def test_print_command_reports_printer_not_ready(mock_print_image):
    """print surfaces printer-not-ready errors on stderr and exits 1."""
    from brother_ptouch_driver import PrinterNotReadyError

    mock_print_image.side_effect = PrinterNotReadyError("Cover open")
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"))
        result = runner.invoke(main, ["print", "label.png", "--tape", "24mm"])

    assert result.exit_code == 1
    assert "Cover open" in result.output


@patch("brother_ptouch_driver.cli.main.print_image")
def test_print_command_reports_transport_error(mock_print_image):
    """print surfaces transport errors on stderr and exits 1."""
    from brother_ptouch_driver import PermissionDeniedError

    mock_print_image.side_effect = PermissionDeniedError("Access denied")
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"))
        result = runner.invoke(main, ["print", "label.png", "--tape", "24mm"])

    assert result.exit_code == 1
    assert "Access denied" in result.output


@patch("brother_ptouch_driver.cli.main.print_image")
def test_print_command_reports_imaging_error(mock_print_image):
    """print surfaces imaging errors on stderr and exits 1."""
    from brother_ptouch_driver.imaging.errors import ImageScalingError

    mock_print_image.side_effect = ImageScalingError("must equal print area")
    runner = CliRunner()

    with runner.isolated_filesystem():
        _write_test_image(Path("label.png"))
        result = runner.invoke(main, ["print", "label.png", "--tape", "24mm"])

    assert result.exit_code == 1
    assert "must equal print area" in result.output
