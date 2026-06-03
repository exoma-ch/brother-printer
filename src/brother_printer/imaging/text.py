"""Text-to-image rendering for label printing."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from brother_printer.imaging.errors import ImagingError
from brother_printer.protocol.enums import TapeWidth

_DEFAULT_FILL_RATIO = 0.8
_METRICS_SAMPLE = "Ay"


def _load_font(font_path: str | None, size: int) -> ImageFont.ImageFont:
    if size < 1:
        msg = "font size must be at least 1"
        raise ValueError(msg)
    if font_path is not None:
        try:
            return ImageFont.truetype(font_path, size)
        except OSError as exc:
            msg = f"failed to load font from {font_path!r}"
            raise ImagingError(msg) from exc
    return ImageFont.load_default(size=size)


def _line_height(font: ImageFont.ImageFont) -> int:
    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    bbox = draw.textbbox((0, 0), _METRICS_SAMPLE, font=font)
    return bbox[3] - bbox[1]


def _block_height(
    font: ImageFont.ImageFont,
    lines: int,
    *,
    line_spacing: float,
) -> int:
    line_h = _line_height(font)
    gap = round(line_spacing * line_h) if lines > 1 else 0
    return lines * line_h + (lines - 1) * gap


def max_font_size(
    tape_width: TapeWidth,
    lines: int,
    *,
    line_spacing: float = 0.0,
    font_path: str | None = None,
    fill_ratio: float = _DEFAULT_FILL_RATIO,
) -> int:
    """Largest font size (px) so stacked lines fit within the tape print area."""
    if lines <= 0:
        msg = "lines must be positive"
        raise ValueError(msg)

    max_block = int(tape_width.print_area_pins * fill_ratio)
    low, high = 1, tape_width.print_area_pins
    best = 0

    while low <= high:
        mid = (low + high) // 2
        font = _load_font(font_path, mid)
        if _block_height(font, lines, line_spacing=line_spacing) <= max_block:
            best = mid
            low = mid + 1
        else:
            high = mid - 1

    if best < 1:
        return 1
    return best
