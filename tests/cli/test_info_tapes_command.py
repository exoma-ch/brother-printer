"""Tests for the brother-printer info tapes CLI command."""

from click.testing import CliRunner

from brother_printer.cli.main import main
from brother_printer.protocol.enums import TapeWidth


def test_info_tapes_lists_all_supported_widths():
    """info tapes prints every TapeWidth with mm label and printable pin count."""
    runner = CliRunner()

    result = runner.invoke(main, ["info", "tapes"])

    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    assert len(lines) == len(TapeWidth)
    for line, width in zip(lines, TapeWidth, strict=True):
        mm, pins = line.split("\t")
        assert mm == f"{width.mm:g} mm"
        assert pins == f"{width.print_area_pins} px"
