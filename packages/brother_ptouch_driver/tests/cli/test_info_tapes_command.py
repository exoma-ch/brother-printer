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
    # One line per width; the self-laminating band is an extra column, not a row.
    assert len(lines) == len(TapeWidth)
    for line, width in zip(lines, TapeWidth, strict=True):
        mm, pins, *_ = line.split("\t")
        assert mm == f"{width.mm:g} mm"
        assert pins == f"{width.print_area_pins} px"


def test_info_tapes_reports_per_width_self_laminating_band():
    """info tapes appends the per-width self-laminating band where measured (issue #50)."""
    runner = CliRunner()

    result = runner.invoke(main, ["info", "tapes"])

    assert result.exit_code == 0
    bands = {}
    for line in result.output.strip().splitlines():
        mm, _pins, *rest = line.split("\t")
        if rest:
            bands[mm] = rest[0]

    assert (
        bands["24 mm"]
        == f"self-laminating: {self_laminating_band_pins(TapeWidth.MM_24)} px"
    )
    assert (
        bands["36 mm"]
        == f"self-laminating: {self_laminating_band_pins(TapeWidth.MM_36)} px"
    )
    # Widths with no measured band carry no extra column.
    assert "12 mm" not in bands
