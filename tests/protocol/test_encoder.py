"""Tests for P-touch raster protocol encoder."""

from pathlib import Path

import pytest

from brother_printer.protocol.constants import (
    CMD_ADVANCED_MODE,
    CMD_COMPRESSION,
    CMD_CUT_EACH,
    CMD_EJECT,
    CMD_INITIALIZE,
    CMD_MARGIN,
    CMD_MODE,
    CMD_PRINT,
    CMD_PRINT_INFO,
    CMD_RASTER,
    CMD_STATUS_REQUEST,
    CMD_SWITCH_RASTER,
    CMD_ZERO_RASTER,
    RASTER_LINE_BYTES,
)
from brother_printer.protocol.encoder import (
    advanced_mode,
    cut_each,
    eject,
    encode_job,
    encode_strip_job,
    initialize,
    invalidate,
    print_information,
    print_page,
    raster_line,
    select_compression,
    set_margin,
    set_mode,
    status_request,
    switch_raster_mode,
    zero_raster,
)
from brother_printer.protocol.enums import TapeWidth

_GOLDEN_DIR = Path(__file__).parent / "golden"


def _load_golden(name: str) -> bytes:
    return (_GOLDEN_DIR / name).read_bytes()


def _blank_raster_line() -> bytes:
    return bytes(RASTER_LINE_BYTES)


def test_invalidate():
    """invalidate() returns 200 null bytes."""
    assert invalidate() == b"\x00" * 200


def test_initialize():
    """initialize() returns ESC @."""
    assert initialize() == CMD_INITIALIZE


def test_status_request():
    """status_request() returns ESC i S."""
    assert status_request() == CMD_STATUS_REQUEST


def test_switch_raster_mode():
    """switch_raster_mode() selects raster command mode."""
    assert switch_raster_mode() == CMD_SWITCH_RASTER


def test_set_mode_auto_cut():
    """set_mode() encodes auto-cut in bit 6."""
    assert set_mode(auto_cut=True) == CMD_MODE + bytes([0x40])
    assert set_mode(auto_cut=False) == CMD_MODE + bytes([0x00])


def test_set_mode_mirror():
    """set_mode() encodes mirror printing in bit 7."""
    assert set_mode(mirror=True) == CMD_MODE + bytes([0x80])


def test_print_information_24mm_single_page():
    """print_information() encodes width, raster count, and last-page role."""
    cmd = print_information(TapeWidth.MM_24, raster_lines=1, last_page=True)
    assert cmd.startswith(CMD_PRINT_INFO)
    assert cmd == (
        CMD_PRINT_INFO
        + bytes([0x06, 0x00, 0x18, 0x00, 0x01, 0x00, 0x00, 0x00, 0x02, 0x00])
    )


def test_print_information_non_last_page():
    """print_information() uses page role 1 for non-last pages."""
    cmd = print_information(TapeWidth.MM_24, raster_lines=10, last_page=False)
    assert cmd[-2] == 0x01


def test_advanced_mode_half_cut_and_no_chain():
    """advanced_mode() sets half-cut and no-chain bits."""
    assert advanced_mode(half_cut=True, no_chain=True) == CMD_ADVANCED_MODE + bytes(
        [0x0C]
    )


def test_cut_each():
    """cut_each() encodes ESC i A with page count byte."""
    assert cut_each(1) == CMD_CUT_EACH + bytes([0x01])
    assert cut_each(3) == CMD_CUT_EACH + bytes([0x03])
    assert cut_each(0) == CMD_CUT_EACH + bytes([0x00])


def test_cut_each_rejects_out_of_range():
    """cut_each() rejects values outside 0..255."""
    with pytest.raises(ValueError, match="cut each"):
        cut_each(-1)
    with pytest.raises(ValueError, match="cut each"):
        cut_each(256)


def test_encode_strip_job_two_pages():
    """encode_strip_job() chains pages with FF between and Control-Z at end."""
    line = _blank_raster_line()
    job = encode_strip_job(
        TapeWidth.MM_24,
        pages=[[line], [line]],
        auto_cut=True,
        half_cut=True,
        no_chain=True,
    )
    assert job.endswith(CMD_EJECT)
    assert CMD_CUT_EACH + bytes([0x02]) in job
    assert advanced_mode(half_cut=True, no_chain=True) in job
    assert job.count(CMD_PRINT_INFO) == 2
    assert print_information(TapeWidth.MM_24, 1, last_page=False) in job
    assert print_information(TapeWidth.MM_24, 1, last_page=True) in job


def test_encode_strip_job_matches_golden():
    """encode_strip_job() with one page matches the single-page golden job."""
    job = encode_strip_job(
        TapeWidth.MM_24,
        pages=[[_blank_raster_line()]],
        auto_cut=True,
        margin_dots=14,
    )
    golden = _load_golden("minimal_job_24mm.bin")
    assert job == golden


def test_encode_strip_job_three_page_golden():
    """encode_strip_job() produces stable bytes for a three-page half-cut strip."""
    line = _blank_raster_line()
    job = encode_strip_job(
        TapeWidth.MM_24,
        pages=[[line], [line], [line]],
        auto_cut=True,
        half_cut=True,
        no_chain=True,
    )
    golden = _load_golden("strip_job_24mm_3page_half_cut.bin")
    assert job == golden


def test_set_margin():
    """set_margin() encodes dot count as little-endian 16-bit."""
    assert set_margin(14) == CMD_MARGIN + bytes([0x0E, 0x00])
    assert set_margin(270) == CMD_MARGIN + bytes([0x0E, 0x01])


def test_set_margin_rejects_out_of_range():
    """set_margin() rejects values outside 16-bit range."""
    with pytest.raises(ValueError, match="margin dots"):
        set_margin(-1)
    with pytest.raises(ValueError, match="margin dots"):
        set_margin(65536)


def test_select_compression():
    """select_compression() prefixes M command with mode byte."""
    assert select_compression(0) == CMD_COMPRESSION + bytes([0x00])
    assert select_compression(2) == CMD_COMPRESSION + bytes([0x02])


def test_raster_line():
    """raster_line() prefixes G command with 70-byte payload length."""
    data = _blank_raster_line()
    cmd = raster_line(data)
    assert cmd == CMD_RASTER + bytes([0x46, 0x00]) + data


def test_raster_line_rejects_wrong_length():
    """raster_line() requires exactly 70 bytes of raster data."""
    with pytest.raises(ValueError, match="70 bytes"):
        raster_line(b"\x00" * 69)


def test_zero_raster():
    """zero_raster() returns Z command."""
    assert zero_raster() == CMD_ZERO_RASTER


def test_print_page_and_eject():
    """print_page() and eject() return fixed single-byte commands."""
    assert print_page() == CMD_PRINT
    assert eject() == CMD_EJECT


def test_encode_job_matches_golden():
    """encode_job() produces the documented minimal 24 mm single-line job."""
    job = encode_job(
        TapeWidth.MM_24,
        raster_lines=[_blank_raster_line()],
        auto_cut=True,
        margin_dots=14,
    )
    golden = _load_golden("minimal_job_24mm.bin")
    assert job == golden


def test_encode_job_idempotent():
    """encode_job() returns identical bytes on repeated calls."""
    kwargs = {
        "width": TapeWidth.MM_24,
        "raster_lines": [_blank_raster_line()],
    }
    assert encode_job(**kwargs) == encode_job(**kwargs)
