"""P-touch raster protocol encoder — pure bytes out, no I/O.

See docs/vendor/ptouch-raster-command-reference.md.
"""

from brother_ptouch_driver.protocol.constants import (
    ADV_HALF_CUT,
    ADV_NO_CHAIN,
    CMD_ADVANCED_MODE,
    CMD_COMPRESSION,
    CMD_CUT_EACH,
    CMD_EJECT,
    CMD_INITIALIZE,
    CMD_INVALIDATE_COUNT,
    CMD_MARGIN,
    CMD_MODE,
    CMD_PRINT,
    CMD_PRINT_INFO,
    CMD_RASTER,
    CMD_STATUS_REQUEST,
    CMD_SWITCH_RASTER,
    CMD_ZERO_RASTER,
    MODE_AUTO_CUT,
    MODE_MIRROR,
    PI_KIND,
    PI_WIDTH,
    RASTER_LINE_BYTES,
)
from brother_ptouch_driver.protocol.enums import TapeWidth

# Laminated/non-laminated tape for ESC i z n2
_MEDIA_TYPE_LAMINATED = 0x00

_PAGE_ROLE_OTHER = 0x01
_PAGE_ROLE_LAST = 0x02


def invalidate() -> bytes:
    """Send 200 null bytes to abort mid-transmission."""
    return b"\x00" * CMD_INVALIDATE_COUNT


def initialize() -> bytes:
    """Initialize printer mode settings (ESC @)."""
    return CMD_INITIALIZE


def status_request() -> bytes:
    """Request 32-byte status reply (ESC i S)."""
    return CMD_STATUS_REQUEST


def switch_raster_mode() -> bytes:
    """Switch printer to raster command mode (ESC i a)."""
    return CMD_SWITCH_RASTER


def set_mode(*, auto_cut: bool = False, mirror: bool = False) -> bytes:
    """Various mode settings — auto-cut and mirror flags (ESC i M)."""
    flags = 0
    if auto_cut:
        flags |= MODE_AUTO_CUT
    if mirror:
        flags |= MODE_MIRROR
    return CMD_MODE + bytes([flags])


def cut_each(n: int) -> bytes:
    """Specify page number in cut each * labels (ESC i A)."""
    if n < 0 or n > 0xFF:
        msg = "cut each n must be 0..255"
        raise ValueError(msg)
    return CMD_CUT_EACH + bytes([n])


def print_information(
    width: TapeWidth,
    raster_lines: int,
    *,
    last_page: bool = True,
    media_type: int = _MEDIA_TYPE_LAMINATED,
) -> bytes:
    """Print information command — media size and page role (ESC i z)."""
    if raster_lines < 0 or raster_lines > 0xFFFFFFFF:
        msg = "raster_lines must fit in 32 bits"
        raise ValueError(msg)
    valid_flags = PI_KIND | PI_WIDTH
    page_role = _PAGE_ROLE_LAST if last_page else _PAGE_ROLE_OTHER
    raster_count = raster_lines.to_bytes(4, "little")
    params = bytes(
        [
            valid_flags,
            media_type,
            width.value,
            0x00,
            *raster_count,
            page_role,
            0x00,
        ]
    )
    return CMD_PRINT_INFO + params


def advanced_mode(*, half_cut: bool = False, no_chain: bool = False) -> bytes:
    """Advanced mode settings — half-cut and no-chain flags (ESC i K)."""
    flags = 0
    if half_cut:
        flags |= ADV_HALF_CUT
    if no_chain:
        flags |= ADV_NO_CHAIN
    return CMD_ADVANCED_MODE + bytes([flags])


def set_margin(dots: int) -> bytes:
    """Specify margin/feed amount in dots (ESC i d)."""
    if dots < 0 or dots > 0xFFFF:
        msg = "margin dots must be 0..65535"
        raise ValueError(msg)
    return CMD_MARGIN + bytes([dots & 0xFF, (dots >> 8) & 0xFF])


def select_compression(mode: int = 0) -> bytes:
    """Select raster compression mode (M)."""
    return CMD_COMPRESSION + bytes([mode & 0xFF])


def raster_line(data: bytes) -> bytes:
    """Transfer one uncompressed raster line (G)."""
    if len(data) != RASTER_LINE_BYTES:
        msg = f"raster data must be exactly {RASTER_LINE_BYTES} bytes"
        raise ValueError(msg)
    length = len(data)
    return CMD_RASTER + bytes([length & 0xFF, (length >> 8) & 0xFF]) + data


def zero_raster() -> bytes:
    """Fill one raster line with zeros (Z); valid in TIFF mode only."""
    return CMD_ZERO_RASTER


def print_page() -> bytes:
    """Print current page without final feed (FF)."""
    return CMD_PRINT


def eject() -> bytes:
    """Print last page with feed/cut per mode settings (Control-Z)."""
    return CMD_EJECT


def _page_cut_settings(
    index: int,
    page_count: int,
    *,
    auto_cut: bool,
    half_cut: bool,
    chunk_size: int | None,
    cut_each_n: int | None,
) -> tuple[bool, bool, int | None]:
    """Resolve ``(auto_cut, half_cut, cut_each_n)`` for one page of a strip.

    Without ``chunk_size`` the whole strip shares one setting. With it, a page
    that closes a chunk — every ``chunk_size``-th page, and the last one — takes
    a full cut, and the pages inside a chunk take ``half_cut`` instead.
    """
    if chunk_size is None:
        effective_auto_cut = auto_cut and not half_cut
        resolved_cut_each = page_count if cut_each_n is None else cut_each_n
        return (
            effective_auto_cut,
            half_cut,
            resolved_cut_each if effective_auto_cut else None,
        )

    closes_chunk = index + 1 == page_count or (index + 1) % chunk_size == 0
    if closes_chunk:
        return True, False, 1
    return False, half_cut, None


def _page_control_block(
    *,
    auto_cut: bool,
    half_cut: bool,
    cut_each_n: int | None,
    no_chain: bool,
) -> bytes:
    """Mode, cut-each and advanced-mode commands that open one strip page."""
    parts = [set_mode(auto_cut=auto_cut)]
    if auto_cut and cut_each_n is not None:
        parts.append(cut_each(cut_each_n))
    parts.append(advanced_mode(half_cut=half_cut, no_chain=no_chain))
    return b"".join(parts)


def encode_strip_job(
    width: TapeWidth,
    pages: list[list[bytes]],
    *,
    auto_cut: bool = True,
    margin_dots: int = 14,
    half_cut: bool = False,
    no_chain: bool = True,
    cut_each_n: int | None = None,
    chunk_size: int | None = None,
    compression: int = 0,
) -> bytes:
    """Assemble a multi-page print job byte stream.

    Half-cut strips disable auto-cut and emit a full control block per page.
    Callers must ensure laminated tape when ``half_cut`` is True; see
    ``print_strip()`` validation in ``brother_ptouch_driver.printing``.

    ``chunk_size`` groups the strip: pages within a chunk are separated by
    half-cuts when ``half_cut`` is True (left uncut otherwise), and every
    chunk boundary — including the end of the strip — takes a full cut. It
    needs ``auto_cut`` and cannot be combined with ``cut_each_n``.
    """
    if not pages:
        msg = "pages must contain at least one raster page"
        raise ValueError(msg)

    if chunk_size is not None:
        if cut_each_n is not None:
            msg = "chunk_size and cut_each_n are mutually exclusive"
            raise ValueError(msg)
        if chunk_size < 1:
            msg = "chunk_size must be at least 1"
            raise ValueError(msg)
        if not auto_cut:
            msg = "chunk_size requires auto_cut"
            raise ValueError(msg)

    if len(pages) == 1:
        return _encode_single_page_job(
            width,
            pages[0],
            auto_cut=auto_cut,
            margin_dots=margin_dots,
            # A one-page strip is its own chunk boundary, so it is full-cut.
            half_cut=half_cut and chunk_size is None,
            no_chain=no_chain,
            compression=compression,
        )

    page_count = len(pages)
    parts: list[bytes] = []

    for index, raster_lines in enumerate(pages):
        is_last = index == page_count - 1
        page_auto_cut, page_half_cut, page_cut_each = _page_cut_settings(
            index,
            page_count,
            auto_cut=auto_cut,
            half_cut=half_cut,
            chunk_size=chunk_size,
            cut_each_n=cut_each_n,
        )
        if index == 0:
            parts.append(initialize())
        parts.append(switch_raster_mode())
        parts.append(print_information(width, len(raster_lines), last_page=is_last))
        parts.extend(
            [
                _page_control_block(
                    auto_cut=page_auto_cut,
                    half_cut=page_half_cut,
                    cut_each_n=page_cut_each,
                    no_chain=no_chain,
                ),
                set_margin(margin_dots),
                select_compression(compression),
            ]
        )
        for line in raster_lines:
            parts.append(raster_line(line))
        parts.append(eject() if is_last else print_page())

    return b"".join(parts)


def _encode_single_page_job(
    width: TapeWidth,
    raster_lines: list[bytes],
    *,
    auto_cut: bool,
    margin_dots: int,
    half_cut: bool,
    no_chain: bool,
    compression: int,
) -> bytes:
    """Assemble a minimal single-page print job byte stream."""
    parts: list[bytes] = [
        initialize(),
        switch_raster_mode(),
        print_information(width, len(raster_lines), last_page=True),
        set_mode(auto_cut=auto_cut),
        advanced_mode(half_cut=half_cut, no_chain=no_chain),
        set_margin(margin_dots),
        select_compression(compression),
    ]
    for line in raster_lines:
        parts.append(raster_line(line))
    parts.append(eject())
    return b"".join(parts)


def encode_job(
    width: TapeWidth,
    raster_lines: list[bytes],
    *,
    auto_cut: bool = True,
    margin_dots: int = 14,
    half_cut: bool = False,
    no_chain: bool = True,
    compression: int = 0,
) -> bytes:
    """Assemble a minimal single-page print job byte stream."""
    return encode_strip_job(
        width,
        [raster_lines],
        auto_cut=auto_cut,
        margin_dots=margin_dots,
        half_cut=half_cut,
        no_chain=no_chain,
        compression=compression,
    )
