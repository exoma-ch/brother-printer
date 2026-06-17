"""Text-to-image rendering for label printing."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

from brother_ptouch_driver.imaging.errors import ImagingError
from brother_ptouch_driver.protocol.enums import TapeWidth

_DEFAULT_FILL_RATIO = 0.8
_MAX_DEFAULT_FONT_SIZE = 48
_METRICS_SAMPLE = "Ay"
_VALID_ROTATIONS = frozenset({0, 90})
_VALID_ALIGNS = frozenset({"left", "center", "right"})
_AUTO_REPLICATE = frozenset({"auto", "fill", "max"})


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
    print_height: int | None = None,
) -> int:
    """Largest font size (px) so text fits within the printable height.

    ``print_height`` overrides the full tape print area with a narrower
    cross-tape pixel budget: a confined band for self-laminating tape, or the
    per-copy band height when a replicated copy must be fitted independently.
    Defaults to ``print_area_pins``.
    """
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

    extent = print_height if print_height is not None else tape_width.print_area_pins
    max_extent = int(extent * fill_ratio)
    low, high = 1, extent
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
    font: ImageFont.ImageFont,
    *,
    align: str,
    line_spacing: float,
    margins: _Margins,
    print_height: int,
) -> Image.Image:
    """Render lines reading along the feed into a canvas ``print_height`` tall."""
    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    max_line_w = _max_line_width(draw, line_list, font)
    image = Image.new(
        "L",
        (
            _label_width(max_line_w, margins=margins, align=align),
            print_height,
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
    print_height: int | None = None,
) -> Image.Image:
    """Render text for 90° rotation: cross-tape width is the printable height."""
    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    max_line_w = _max_line_width(draw, line_list, font)
    cross_tape = (
        print_height if print_height is not None else tape_width.print_area_pins
    )
    content_w = cross_tape - margins.left - margins.right
    if max_line_w > content_w:
        msg = (
            f"text width {max_line_w}px exceeds printable width "
            f"{content_w}px for {tape_width.mm}mm tape"
        )
        raise ImagingError(msg)

    block_h = _block_height(font, len(line_list), line_spacing=line_spacing)
    image = Image.new(
        "L",
        (cross_tape, block_h + margins.vertical),
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


def _effective_height(tape_width: TapeWidth, print_height: int | None) -> int:
    """Cross-tape pixel budget: the confined band or the full print area."""
    return print_height if print_height is not None else tape_width.print_area_pins


def _resolve_font_size(
    line_list: list[str],
    tape_width: TapeWidth,
    *,
    font_size: int | None,
    font_path: str | None,
    line_spacing: float,
    fill_ratio: float,
    rotate: int,
    print_height: int | None,
) -> int:
    if font_size is not None:
        if font_size < 1:
            msg = "font size must be at least 1"
            raise ValueError(msg)
        return font_size
    fitted = max_font_size(
        tape_width,
        len(line_list),
        line_spacing=line_spacing,
        font_path=font_path,
        fill_ratio=fill_ratio,
        rotate=rotate,
        samples=line_list,
        print_height=print_height,
    )
    return min(fitted, _MAX_DEFAULT_FONT_SIZE)


def _tile_vertical(
    unit: Image.Image, total_height: int, count: int, band_extent: int
) -> Image.Image:
    """Stack ``count`` copies of ``unit`` down the tape-width axis."""
    canvas = Image.new("L", (unit.width, total_height), 255)
    for index in range(count):
        canvas.paste(unit, (0, index * band_extent))
    return canvas


def _tile_horizontal(unit: Image.Image, count: int) -> Image.Image:
    """Repeat ``count`` copies of ``unit`` along the feed axis."""
    canvas = Image.new("L", (unit.width * count, unit.height), 255)
    for index in range(count):
        canvas.paste(unit, (index * unit.width, 0))
    return canvas


def _render_replicated_horizontal(
    line_list: list[str],
    tape_width: TapeWidth,
    replicate: int,
    *,
    font_path: str | None,
    font_size: int | None,
    align: str,
    line_spacing: float,
    margins: _Margins,
    fill_ratio: float,
    print_height: int | None,
) -> Image.Image:
    """Render text reading along the feed, copies stacked across the width."""
    total = _effective_height(tape_width, print_height)
    band_extent = total // replicate
    if band_extent < 1:
        msg = (
            f"replicate={replicate} exceeds the {total}px printable height "
            f"of {tape_width.mm}mm tape"
        )
        raise ImagingError(msg)
    size = _resolve_font_size(
        line_list,
        tape_width,
        font_size=font_size,
        font_path=font_path,
        line_spacing=line_spacing,
        fill_ratio=fill_ratio,
        rotate=0,
        print_height=band_extent,
    )
    font = _load_font(font_path, size)
    unit = _render_horizontal(
        line_list,
        font,
        align=align,
        line_spacing=line_spacing,
        margins=margins,
        print_height=band_extent,
    )
    if replicate == 1:
        return unit
    return _tile_vertical(unit, total, replicate, band_extent)


def _render_replicated_rotated(
    line_list: list[str],
    tape_width: TapeWidth,
    replicate: int,
    *,
    font_path: str | None,
    font_size: int | None,
    align: str,
    line_spacing: float,
    margins: _Margins,
    fill_ratio: float,
    print_height: int | None,
) -> Image.Image:
    """Render text reading across the width, copies repeated along the feed."""
    size = _resolve_font_size(
        line_list,
        tape_width,
        font_size=font_size,
        font_path=font_path,
        line_spacing=line_spacing,
        fill_ratio=fill_ratio,
        rotate=90,
        print_height=print_height,
    )
    font = _load_font(font_path, size)
    unit = _render_rotated_90(
        line_list,
        tape_width,
        font,
        align=align,
        line_spacing=line_spacing,
        margins=margins,
        print_height=print_height,
    )
    if replicate == 1:
        return unit
    return _tile_horizontal(unit, replicate)


def _resolve_replicate(
    replicate: int | str,
    line_list: list[str],
    tape_width: TapeWidth,
    *,
    rotate: int,
    font_path: str | None,
    font_size: int | None,
    line_spacing: float,
    margins: _Margins,
    fixed_width: int | None,
    print_height: int | None,
) -> int:
    """Resolve an explicit copy count or an ``"auto"`` fill request to an int."""
    if not isinstance(replicate, str):
        if replicate < 1:
            msg = "replicate must be at least 1"
            raise ImagingError(msg)
        return replicate

    if replicate.strip().lower() not in _AUTO_REPLICATE:
        msg = f"replicate must be a positive integer or 'auto', got {replicate!r}"
        raise ImagingError(msg)
    if font_size is None:
        msg = "automatic replication requires an explicit font_size"
        raise ImagingError(msg)

    font = _load_font(font_path, font_size)
    if rotate == 0:
        total = _effective_height(tape_width, print_height)
        per_copy = (
            _block_height(font, len(line_list), line_spacing=line_spacing)
            + margins.vertical
        )
        return max(1, total // max(1, per_copy))

    if fixed_width is None:
        msg = "automatic replication with rotation requires fixed_width"
        raise ImagingError(msg)
    unit = _render_rotated_90(
        line_list,
        tape_width,
        font,
        align="center",
        line_spacing=line_spacing,
        margins=margins,
        print_height=print_height,
    )
    return max(1, fixed_width // max(1, unit.width))


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
    replicate: int | str = 1,
    fill_ratio: float = _DEFAULT_FILL_RATIO,
    print_height: int | None = None,
) -> Image.Image:
    """Render multi-line text to a grayscale image sized for the tape width.

    ``print_height`` confines text to a narrower cross-tape band than the full
    tape print area (self-laminating tape); defaults to the full print area.

    ``replicate`` repeats the text that many times along the axis perpendicular
    to its reading direction, producing a single label that stays legible when
    wrapped around a cable. Without ``rotate`` the copies stack across the
    printable height (so each shrinks to fit ``print_height / replicate``); with
    ``rotate=90`` the copies repeat along the feed axis at full width.

    Pass ``replicate="auto"`` to fit as many copies as the tape and font allow
    (requires an explicit ``font_size``; the rotated variant also needs
    ``fixed_width`` to bound the feed axis).
    """
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
    replicate_count = _resolve_replicate(
        replicate,
        line_list,
        tape_width,
        rotate=rotate,
        font_path=font_path,
        font_size=font_size,
        line_spacing=line_spacing,
        margins=margins,
        fixed_width=fixed_width,
        print_height=print_height,
    )
    replicate_kwargs = {
        "font_path": font_path,
        "font_size": font_size,
        "align": align,
        "line_spacing": line_spacing,
        "margins": margins,
        "fill_ratio": fill_ratio,
        "print_height": print_height,
    }

    if rotate == 0:
        image = _render_replicated_horizontal(
            line_list, tape_width, replicate_count, **replicate_kwargs
        )
    else:
        image = _render_replicated_rotated(
            line_list, tape_width, replicate_count, **replicate_kwargs
        )

    if fixed_width is not None:
        image = _apply_fixed_width(image, fixed_width, align=align)

    return image
