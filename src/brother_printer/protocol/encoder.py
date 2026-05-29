"""P-touch raster protocol encoder — pure bytes out, no I/O.

See docs/vendor/ptouch-raster-command-reference.md.
"""

from brother_printer.protocol.constants import (
    ADV_HALF_CUT,
    ADV_NO_CHAIN,
    CMD_ADVANCED_MODE,
    CMD_COMPRESSION,
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
from brother_printer.protocol.enums import TapeWidth

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


def encode_job(
    width: TapeWidth,
    raster_lines: list[bytes],
    *,
    auto_cut: bool = True,
    margin_dots: int = 14,
    half_cut: bool = False,
    no_chain: bool = False,
    compression: int = 0,
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
