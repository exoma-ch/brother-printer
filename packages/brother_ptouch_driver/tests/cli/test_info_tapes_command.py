"""Tests for the brother-ptouch-driver info tapes CLI command."""

from click.testing import CliRunner

from brother_ptouch_driver.cli.main import main
from brother_ptouch_driver.protocol.enums import TapeWidth, self_laminating_band_pins


def test_info_tapes_lists_all_supported_widths():
    """info tapes prints every TapeWidth with mm label and printable pin count."""
    runner = CliRunner()

    result = runner.invoke(main, ["info", "tapes"])

    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    # One line per width, plus a trailing self-laminating band line.
    assert len(lines) == len(TapeWidth) + 1
    for line, width in zip(lines[:-1], TapeWidth, strict=True):
        mm, pins = line.split("\t")
        assert mm == f"{width.mm:g} mm"
        assert pins == f"{width.print_area_pins} px"


def test_info_tapes_reports_self_laminating_band():
    """info tapes reports the self-laminating printable band (issue #41)."""
    runner = CliRunner()

    result = runner.invoke(main, ["info", "tapes"])

    assert result.exit_code == 0
    label, pins = result.output.strip().splitlines()[-1].split("\t")
    assert label == "self-laminating"
    assert pins == f"{self_laminating_band_pins()} px"
    assert self_laminating_band_pins() == 140
