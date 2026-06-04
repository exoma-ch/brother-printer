"""Text-to-image rendering for label printing."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from brother_printer.imaging.errors import ImagingError
from brother_printer.protocol.enums import TapeWidth

_DEFAULT_FILL_RATIO = 0.8
_MIN_DEFAULT_FONT_SIZE = 50
_METRICS_SAMPLE = "Ay"
_VALID_ROTATIONS = frozenset({0, 90, 180, 270})
_VALID_ALIGNS = frozenset({"left", "center", "right"})


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


def _textbbox(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont
) -> tuple[int, int, int, int]:
    return draw.textbbox((0, 0), text, font=font)


def _line_width(draw: ImageDraw.ImageDraw, line: str, font: ImageFont.ImageFont) -> int:
    bbox = _textbbox(draw, line, font)
    return bbox[2] - bbox[0]


def _x_for_align(
    align: str,
    *,
    margin: int,
    content_width: int,
    bbox: tuple[int, int, int, int],
) -> int:
    text_width = bbox[2] - bbox[0]
    if align == "left":
        return margin - bbox[0]
    if align == "right":
        return margin + content_width - bbox[2]
    return margin + (content_width - text_width) // 2 - bbox[0]


def _draw_stacked_lines(
    image: Image.Image,
    line_list: list[str],
    font: ImageFont.ImageFont,
    *,
    align: str,
    line_spacing: float,
    margin: int,
) -> None:
    """Draw lines stacked along the image y axis."""
    draw = ImageDraw.Draw(image)
    line_h = _line_height(font)
    gap = round(line_spacing * line_h) if len(line_list) > 1 else 0
    block_h = _block_height(font, len(line_list), line_spacing=line_spacing)

    content_width = image.width - 2 * margin
    y_start = (image.height - block_h) // 2
    y = y_start
    for line in line_list:
        bbox = _textbbox(draw, line, font)
        x = _x_for_align(align, margin=margin, content_width=content_width, bbox=bbox)
        draw.text((x, y - bbox[1]), line, font=font, fill=0)
        y += line_h + gap


def _label_width(max_line_w: int, *, margin: int, align: str) -> int:
    """Canvas width along the label feed axis (room for horizontal alignment)."""
    align_slack = 0 if align == "center" else max_line_w
    return max_line_w + 2 * margin + align_slack


def _render_horizontal(
    line_list: list[str],
    tape_width: TapeWidth,
    font: ImageFont.ImageFont,
    *,
    align: str,
    line_spacing: float,
    margin: int,
) -> Image.Image:
    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    max_line_w = max(_line_width(draw, line, font) for line in line_list)
    image = Image.new(
        "L",
        (
            _label_width(max_line_w, margin=margin, align=align),
            tape_width.print_area_pins,
        ),
        255,
    )
    _draw_stacked_lines(
        image,
        line_list,
        font,
        align=align,
        line_spacing=line_spacing,
        margin=margin,
    )
    return image


def render_text(
    text: str,
    tape_width: TapeWidth,
    *,
    font_path: str | None = None,
    font_size: int | None = None,
    align: str = "center",
    line_spacing: float = 0.0,
    rotate: int = 0,
    margin: int = 0,
    fill_ratio: float = _DEFAULT_FILL_RATIO,
) -> Image.Image:
    """Render multi-line text to a grayscale image sized for the tape width."""
    if not text.strip() or all(not line.strip() for line in text.split("\n")):
        msg = "text must not be empty"
        raise ImagingError(msg)
    if align not in _VALID_ALIGNS:
        msg = f"align must be one of {sorted(_VALID_ALIGNS)}, got {align!r}"
        raise ImagingError(msg)
    if rotate not in _VALID_ROTATIONS:
        msg = f"rotation must be one of {sorted(_VALID_ROTATIONS)}, got {rotate}"
        raise ImagingError(msg)
    if margin < 0:
        msg = "margin must be non-negative"
        raise ImagingError(msg)

    line_list = text.split("\n")
    if font_size is None:
        size = max(
            max_font_size(
                tape_width,
                len(line_list),
                line_spacing=line_spacing,
                font_path=font_path,
                fill_ratio=fill_ratio,
            ),
            _MIN_DEFAULT_FONT_SIZE,
        )
    else:
        if font_size < 1:
            msg = "font size must be at least 1"
            raise ValueError(msg)
        size = font_size

    font = _load_font(font_path, size)
    render_kwargs = {
        "align": align,
        "line_spacing": line_spacing,
        "margin": margin,
    }

    image = _render_horizontal(line_list, tape_width, font, **render_kwargs)
    if rotate in {180, 270}:
        return image.rotate(180, expand=False, resample=Image.Resampling.NEAREST)
    return image
