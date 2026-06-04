"""Text-to-image rendering for label printing."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

from brother_ptouch_driver.imaging.errors import ImagingError
from brother_ptouch_driver.protocol.enums import TapeWidth

_DEFAULT_FILL_RATIO = 0.8
_MIN_DEFAULT_FONT_SIZE = 50
_METRICS_SAMPLE = "Ay"
_VALID_ROTATIONS = frozenset({0, 90})
_VALID_ALIGNS = frozenset({"left", "center", "right"})


@dataclass(frozen=True)
class _Margins:
    top: int
    bottom: int
    left: int
    right: int

    @property
    def horizontal(self) -> int:
        return self.left + self.right

    @property
    def vertical(self) -> int:
        return self.top + self.bottom


def _resolve_margins(
    *,
    margin: int = 0,
    margin_top: int | None = None,
    margin_bottom: int | None = None,
    margin_left: int | None = None,
    margin_right: int | None = None,
) -> _Margins:
    if margin < 0:
        msg = "margin must be non-negative"
        raise ImagingError(msg)
    for name, value in (
        ("margin_top", margin_top),
        ("margin_bottom", margin_bottom),
        ("margin_left", margin_left),
        ("margin_right", margin_right),
    ):
        if value is not None and value < 0:
            msg = f"{name} must be non-negative"
            raise ImagingError(msg)

    base = margin
    return _Margins(
        top=margin_top if margin_top is not None else base,
        bottom=margin_bottom if margin_bottom is not None else base,
        left=margin_left if margin_left is not None else base,
        right=margin_right if margin_right is not None else base,
    )


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


def _max_line_width(
    draw: ImageDraw.ImageDraw,
    line_list: list[str],
    font: ImageFont.ImageFont,
) -> int:
    return max(_line_width(draw, line, font) for line in line_list)


def max_font_size(
    tape_width: TapeWidth,
    lines: int,
    *,
    line_spacing: float = 0.0,
    font_path: str | None = None,
    fill_ratio: float = _DEFAULT_FILL_RATIO,
    rotate: int = 0,
    samples: list[str] | None = None,
) -> int:
    """Largest font size (px) so text fits within the tape print area."""
    if lines <= 0:
        msg = "lines must be positive"
        raise ValueError(msg)
    if rotate not in _VALID_ROTATIONS:
        msg = f"rotation must be one of {sorted(_VALID_ROTATIONS)}, got {rotate}"
        raise ValueError(msg)

    sample_lines = samples if samples is not None else ["Ay"] * lines
    if len(sample_lines) != lines:
        msg = "samples length must match lines"
        raise ValueError(msg)

    max_extent = int(tape_width.print_area_pins * fill_ratio)
    low, high = 1, tape_width.print_area_pins
    best = 0

    while low <= high:
        mid = (low + high) // 2
        font = _load_font(font_path, mid)
        if rotate == 0:
            fits = _block_height(font, lines, line_spacing=line_spacing) <= max_extent
        else:
            draw = ImageDraw.Draw(Image.new("L", (1, 1)))
            fits = _max_line_width(draw, sample_lines, font) <= max_extent
        if fits:
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
    margin_left: int,
    content_width: int,
    bbox: tuple[int, int, int, int],
) -> int:
    text_width = bbox[2] - bbox[0]
    if align == "left":
        return margin_left - bbox[0]
    if align == "right":
        return margin_left + content_width - bbox[2]
    return margin_left + (content_width - text_width) // 2 - bbox[0]


def _draw_stacked_lines(
    image: Image.Image,
    line_list: list[str],
    font: ImageFont.ImageFont,
    *,
    align: str,
    line_spacing: float,
    margins: _Margins,
) -> None:
    """Draw lines stacked along the image y axis."""
    draw = ImageDraw.Draw(image)
    line_h = _line_height(font)
    gap = round(line_spacing * line_h) if len(line_list) > 1 else 0
    block_h = _block_height(font, len(line_list), line_spacing=line_spacing)

    content_width = image.width - margins.left - margins.right
    y_start = margins.top + (image.height - margins.vertical - block_h) // 2
    y = y_start
    for line in line_list:
        bbox = _textbbox(draw, line, font)
        x = _x_for_align(
            align,
            margin_left=margins.left,
            content_width=content_width,
            bbox=bbox,
        )
        draw.text((x, y - bbox[1]), line, font=font, fill=0)
        y += line_h + gap


def _label_width(
    max_line_w: int,
    *,
    margins: _Margins,
    align: str,
) -> int:
    """Canvas width along the label feed axis (room for horizontal alignment)."""
    align_slack = 0 if align == "center" else max_line_w
    return max_line_w + margins.horizontal + align_slack


def _render_horizontal(
    line_list: list[str],
    tape_width: TapeWidth,
    font: ImageFont.ImageFont,
    *,
    align: str,
    line_spacing: float,
    margins: _Margins,
) -> Image.Image:
    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    max_line_w = _max_line_width(draw, line_list, font)
    image = Image.new(
        "L",
        (
            _label_width(max_line_w, margins=margins, align=align),
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
        margins=margins,
    )
    return image


def _render_rotated_90(
    line_list: list[str],
    tape_width: TapeWidth,
    font: ImageFont.ImageFont,
    *,
    align: str,
    line_spacing: float,
    margins: _Margins,
) -> Image.Image:
    """Render text for 90° rotation: cross-tape width is print_area_pins."""
    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    max_line_w = _max_line_width(draw, line_list, font)
    content_w = tape_width.print_area_pins - margins.left - margins.right
    if max_line_w > content_w:
        msg = (
            f"text width {max_line_w}px exceeds printable width "
            f"{content_w}px for {tape_width.mm}mm tape"
        )
        raise ImagingError(msg)

    block_h = _block_height(font, len(line_list), line_spacing=line_spacing)
    image = Image.new(
        "L",
        (tape_width.print_area_pins, block_h + margins.vertical),
        255,
    )
    _draw_stacked_lines(
        image,
        line_list,
        font,
        align=align,
        line_spacing=line_spacing,
        margins=margins,
    )
    return image.rotate(90, expand=True, resample=Image.Resampling.NEAREST)


def _apply_fixed_width(
    image: Image.Image,
    fixed_width: int,
    *,
    align: str,
) -> Image.Image:
    if image.width > fixed_width:
        msg = f"rendered width {image.width}px exceeds fixed width {fixed_width}px"
        raise ImagingError(msg)
    if image.width == fixed_width:
        return image

    canvas = Image.new("L", (fixed_width, image.height), 255)
    if align == "left":
        x = 0
    elif align == "right":
        x = fixed_width - image.width
    else:
        x = (fixed_width - image.width) // 2
    canvas.paste(image, (x, 0))
    return canvas


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
    margin_top: int | None = None,
    margin_bottom: int | None = None,
    margin_left: int | None = None,
    margin_right: int | None = None,
    fixed_width: int | None = None,
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
    if fixed_width is not None and fixed_width < 1:
        msg = "fixed_width must be at least 1"
        raise ImagingError(msg)

    margins = _resolve_margins(
        margin=margin,
        margin_top=margin_top,
        margin_bottom=margin_bottom,
        margin_left=margin_left,
        margin_right=margin_right,
    )

    line_list = text.split("\n")
    if font_size is None:
        fitted = max_font_size(
            tape_width,
            len(line_list),
            line_spacing=line_spacing,
            font_path=font_path,
            fill_ratio=fill_ratio,
            rotate=rotate,
            samples=line_list,
        )
        if rotate == 0:
            size = max(fitted, _MIN_DEFAULT_FONT_SIZE)
        else:
            size = fitted
    else:
        if font_size < 1:
            msg = "font size must be at least 1"
            raise ValueError(msg)
        size = font_size

    font = _load_font(font_path, size)
    render_kwargs = {
        "align": align,
        "line_spacing": line_spacing,
        "margins": margins,
    }

    if rotate == 0:
        image = _render_horizontal(line_list, tape_width, font, **render_kwargs)
    else:
        image = _render_rotated_90(line_list, tape_width, font, **render_kwargs)

    if fixed_width is not None:
        image = _apply_fixed_width(image, fixed_width, align=align)

    return image
