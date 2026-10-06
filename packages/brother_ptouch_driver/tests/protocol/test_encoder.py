"""Tests for P-touch raster protocol encoder."""

from pathlib import Path

import pytest

from brother_ptouch_driver.protocol.constants import (
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
from brother_ptouch_driver.protocol.encoder import (
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
from brother_ptouch_driver.protocol.enums import TapeWidth

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
    adv = advanced_mode(half_cut=True, no_chain=True)
    assert job.endswith(CMD_EJECT)
    assert CMD_CUT_EACH not in job
    assert job.count(set_mode(auto_cut=False)) == 2
    assert job.count(adv) == 2
    assert job.index(CMD_PRINT_INFO) < job.index(adv)
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


def test_encode_strip_job_half_cut_disables_auto_cut():
    """Half-cut strips disable auto-cut and omit cut-each; full-cut strips unchanged."""
    line = _blank_raster_line()
    half_cut_job = encode_strip_job(
        TapeWidth.MM_24,
        pages=[[line], [line], [line]],
        auto_cut=True,
        half_cut=True,
        no_chain=True,
    )
    adv = advanced_mode(half_cut=True, no_chain=True)
    assert CMD_CUT_EACH not in half_cut_job
    assert half_cut_job.count(set_mode(auto_cut=False)) == 3
    assert half_cut_job.count(adv) == 3
    assert half_cut_job.index(CMD_PRINT_INFO) < half_cut_job.index(adv)

    full_cut_job = encode_strip_job(
        TapeWidth.MM_24,
        pages=[[line], [line], [line]],
        auto_cut=True,
        half_cut=False,
        no_chain=True,
    )
    cut_each_3 = CMD_CUT_EACH + bytes([0x03])
    assert full_cut_job.count(cut_each_3) == 3
    assert full_cut_job.count(set_mode(auto_cut=True)) == 3


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


def _half_cut_block() -> bytes:
    """Control block of a page that ends in a half cut."""
    return set_mode(auto_cut=False) + advanced_mode(half_cut=True, no_chain=True)


def _full_cut_block() -> bytes:
    """Control block of a page that ends in a full cut."""
    return (
        set_mode(auto_cut=True)
        + cut_each(1)
        + advanced_mode(half_cut=False, no_chain=True)
    )


def _no_cut_block() -> bytes:
    """Control block of a page that is not cut at all."""
    return set_mode(auto_cut=False) + advanced_mode(half_cut=False, no_chain=True)


def test_encode_strip_job_chunk_size_half_cuts_within_chunks():
    """chunk_size half-cuts inside a chunk and full-cuts at every boundary."""
    line = _blank_raster_line()
    job = encode_strip_job(
        TapeWidth.MM_24,
        pages=[[line]] * 5,
        auto_cut=True,
        half_cut=True,
        no_chain=True,
        chunk_size=2,
    )

    # Pages 2, 4 close a chunk and page 5 is last: three full cuts, two half cuts.
    assert job.count(_full_cut_block()) == 3
    assert job.count(_half_cut_block()) == 2
    assert job.count(CMD_PRINT_INFO) == 5
    assert job.count(print_information(TapeWidth.MM_24, 1, last_page=False)) == 4
    assert job.count(print_information(TapeWidth.MM_24, 1, last_page=True)) == 1
    assert job.endswith(CMD_EJECT)


def test_encode_strip_job_chunk_size_without_half_cut_cuts_only_at_boundaries():
    """chunk_size without half_cut leaves interior pages uncut."""
    line = _blank_raster_line()
    job = encode_strip_job(
        TapeWidth.MM_24,
        pages=[[line]] * 5,
        auto_cut=True,
        half_cut=False,
        no_chain=True,
        chunk_size=2,
    )

    assert job.count(_full_cut_block()) == 3
    assert job.count(_no_cut_block()) == 2
    assert advanced_mode(half_cut=True, no_chain=True) not in job


def test_encode_strip_job_chunk_size_one_cuts_every_page():
    """chunk_size=1 makes every page a chunk boundary."""
    line = _blank_raster_line()
    job = encode_strip_job(
        TapeWidth.MM_24,
        pages=[[line]] * 3,
        auto_cut=True,
        half_cut=True,
        no_chain=True,
        chunk_size=1,
    )

    assert job.count(_full_cut_block()) == 3
    assert _half_cut_block() not in job


def test_encode_strip_job_chunk_size_leaves_default_behavior_untouched():
    """chunk_size=None keeps the established half-cut and full-cut strip streams."""
    line = _blank_raster_line()
    pages = [[line]] * 3
    kwargs = {"auto_cut": True, "no_chain": True}

    assert encode_strip_job(
        TapeWidth.MM_24, pages=pages, half_cut=True, chunk_size=None, **kwargs
    ) == encode_strip_job(TapeWidth.MM_24, pages=pages, half_cut=True, **kwargs)
    assert encode_strip_job(
        TapeWidth.MM_24, pages=pages, half_cut=False, chunk_size=None, **kwargs
    ) == encode_strip_job(TapeWidth.MM_24, pages=pages, half_cut=False, **kwargs)


def test_encode_strip_job_chunk_size_single_page_is_full_cut():
    """A one-page chunked strip is its own boundary, so it takes a full cut."""
    job = encode_strip_job(
        TapeWidth.MM_24,
        pages=[[_blank_raster_line()]],
        auto_cut=True,
        half_cut=True,
        margin_dots=14,
        chunk_size=4,
    )

    assert job == _load_golden("minimal_job_24mm.bin")


def test_encode_strip_job_rejects_invalid_chunk_size():
    """chunk_size must be a positive page count."""
    pages = [[_blank_raster_line()]] * 2
    for invalid in (0, -1):
        with pytest.raises(ValueError, match="chunk_size"):
            encode_strip_job(TapeWidth.MM_24, pages=pages, chunk_size=invalid)


def test_encode_strip_job_chunk_size_requires_auto_cut():
    """Chunk boundaries are auto-cuts, so chunk_size needs auto_cut enabled."""
    pages = [[_blank_raster_line()]] * 2
    with pytest.raises(ValueError, match="chunk_size requires auto_cut"):
        encode_strip_job(TapeWidth.MM_24, pages=pages, auto_cut=False, chunk_size=2)


def test_encode_strip_job_rejects_chunk_size_with_cut_each_n():
    """chunk_size and cut_each_n both drive full cuts; refuse the ambiguity."""
    pages = [[_blank_raster_line()]] * 2
    with pytest.raises(ValueError, match="mutually exclusive"):
        encode_strip_job(TapeWidth.MM_24, pages=pages, chunk_size=2, cut_each_n=2)


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
