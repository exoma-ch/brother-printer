"""Tests for text rendering and max font size helpers."""

from __future__ import annotations

import pytest
from PIL import Image, ImageDraw, ImageFont

from brother_printer.imaging.errors import ImagingError
from brother_printer.imaging.raster import image_to_raster
from brother_printer.protocol.constants import RASTER_LINE_BYTES
from brother_printer.protocol.encoder import encode_job, raster_line
from brother_printer.protocol.enums import TapeWidth
from brother_printer_text.text import max_font_size, render_text

_ALL_TAPES = list(TapeWidth)
_ALL_ROTATIONS = [0, 90, 180, 270]

_FILL_RATIO = 0.8


def _line_height(font: ImageFont.ImageFont) -> int:
    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    bbox = draw.textbbox((0, 0), "Ay", font=font)
    return bbox[3] - bbox[1]


def _block_height(
    size: int,
    lines: int,
    *,
    line_spacing: float = 0.0,
    font_path: str | None = None,
) -> int:
    if font_path:
        font = ImageFont.truetype(font_path, size)
    else:
        font = ImageFont.load_default(size=size)
    line_h = _line_height(font)
    gap = round(line_spacing * line_h) if lines > 1 else 0
    return lines * line_h + (lines - 1) * gap


def _max_allowed(tape_width: TapeWidth) -> int:
    return int(tape_width.print_area_pins * _FILL_RATIO)


@pytest.mark.parametrize(
    ("tape_width", "lines"),
    [
        (TapeWidth.MM_12, 1),
        (TapeWidth.MM_12, 2),
        (TapeWidth.MM_24, 1),
        (TapeWidth.MM_24, 3),
        (TapeWidth.MM_36, 1),
    ],
)
def test_max_font_size_returns_positive_int(tape_width, lines):
    """max_font_size returns a positive integer for valid inputs."""
    size = max_font_size(tape_width, lines)
    assert isinstance(size, int)
    assert size >= 1


@pytest.mark.parametrize(
    ("tape_width", "lines"),
    [
        (TapeWidth.MM_12, 1),
        (TapeWidth.MM_12, 2),
        (TapeWidth.MM_24, 1),
        (TapeWidth.MM_24, 3),
        (TapeWidth.MM_36, 1),
    ],
)
def test_max_font_size_fits_print_area(tape_width, lines):
    """Returned size keeps the text block within print_area_pins * fill_ratio."""
    size = max_font_size(tape_width, lines)
    block = _block_height(size, lines)
    assert block <= _max_allowed(tape_width)


@pytest.mark.parametrize(
    "tape_width", [TapeWidth.MM_12, TapeWidth.MM_24, TapeWidth.MM_36]
)
def test_max_font_size_is_maximal(tape_width):
    """size + 1 exceeds the allowed block height."""
    size = max_font_size(tape_width, 1)
    block_next = _block_height(size + 1, 1)
    assert block_next > _max_allowed(tape_width)


def test_max_font_size_more_lines_yields_smaller_size():
    """More lines require a smaller font to fit the tape height."""
    tape = TapeWidth.MM_24
    one_line = max_font_size(tape, 1)
    three_lines = max_font_size(tape, 3)
    assert three_lines < one_line


def test_max_font_size_larger_line_spacing_yields_smaller_size():
    """Increased line spacing reduces the maximum fitting font size."""
    tape = TapeWidth.MM_24
    tight = max_font_size(tape, 2, line_spacing=0.0)
    loose = max_font_size(tape, 2, line_spacing=0.5)
    assert loose < tight


@pytest.mark.parametrize("lines", [0, -1])
def test_max_font_size_rejects_invalid_line_count(lines):
    """lines must be positive."""
    with pytest.raises(ValueError, match="lines"):
        max_font_size(TapeWidth.MM_24, lines)


def _ink_centroid_x(image: Image.Image) -> float:
    pixels = image.load()
    assert pixels is not None
    xs = [
        x for x in range(image.width) for y in range(image.height) if pixels[x, y] < 128
    ]
    if not xs:
        return image.width / 2
    return sum(xs) / len(xs)


def _ink_pixel_count(image: Image.Image) -> int:
    pixels = image.load()
    assert pixels is not None
    return sum(
        1 for x in range(image.width) for y in range(image.height) if pixels[x, y] < 128
    )


@pytest.mark.parametrize("tape_width", _ALL_TAPES)
@pytest.mark.parametrize("rotate", _ALL_ROTATIONS)
def test_render_text_height_matches_tape(tape_width, rotate):
    """Rendered image height always equals print_area_pins."""
    image = render_text("Hello", tape_width, rotate=rotate)
    assert image.height == tape_width.print_area_pins


def test_render_text_width_grows_with_longer_text():
    """Longer single-line text produces a wider label."""
    tape = TapeWidth.MM_24
    short = render_text("Hi", tape)
    long = render_text("Hello World!", tape)
    assert long.width > short.width


def test_render_text_multiline_keeps_tape_height():
    """Multi-line text still fits the tape cross-section height."""
    tape = TapeWidth.MM_24
    image = render_text("Line1\nLine2\nLine3", tape)
    assert image.height == tape.print_area_pins


@pytest.mark.parametrize(
    ("align", "relation"),
    [
        ("left", "less"),
        ("center", "approx"),
        ("right", "greater"),
    ],
)
def test_render_text_align_shifts_ink_centroid(align, relation):
    """Horizontal alignment shifts where ink sits along the label length."""
    tape = TapeWidth.MM_24
    wide = render_text("ABCDEFGH", tape, align=align, font_size=40, margin=80)
    centroid = _ink_centroid_x(wide)
    mid = wide.width / 2
    if relation == "less":
        assert centroid < mid - 20
    elif relation == "greater":
        assert centroid > mid + 20
    else:
        assert abs(centroid - mid) < 20


def test_render_text_explicit_font_size_increases_ink():
    """A larger explicit font_size produces more ink than auto-fit."""
    tape = TapeWidth.MM_24
    auto = render_text("Test", tape)
    large = render_text("Test", tape, font_size=max_font_size(tape, 1))
    assert _ink_pixel_count(large) >= _ink_pixel_count(auto)


def test_render_text_rotate_90_matches_zero():
    """90-degree rotation renders the same full-length label as 0 degrees."""
    tape = TapeWidth.MM_24
    flat = render_text("Rotate", tape, rotate=0)
    turned = render_text("Rotate", tape, rotate=90)
    assert turned.size == flat.size
    assert turned.tobytes() == flat.tobytes()
    assert _ink_pixel_count(turned) == _ink_pixel_count(flat)


def test_render_text_rotate_270_matches_180():
    """270-degree rotation renders the same full-length label as 180 degrees."""
    tape = TapeWidth.MM_24
    upside_down = render_text("Rotate", tape, rotate=180)
    turned = render_text("Rotate", tape, rotate=270)
    assert turned.size == upside_down.size
    assert turned.tobytes() == upside_down.tobytes()


def test_render_text_rotate_90_preserves_full_text_on_wide_tape():
    """Regression: rotated text must not be cropped on wide tape."""
    tape = TapeWidth.MM_36
    flat = render_text("Hello Lars", tape, rotate=0)
    turned = render_text("Hello Lars", tape, rotate=90)
    assert turned.width == flat.width
    assert _ink_pixel_count(turned) == _ink_pixel_count(flat)


def test_render_text_default_font_size_floors_small_tape():
    """Default font size is at least 50px even when max_font_size is smaller."""
    tape = TapeWidth.MM_3_5
    assert max_font_size(tape, 1) < 50
    default = render_text("Hi", tape)
    floored = render_text("Hi", tape, font_size=50)
    assert default.tobytes() == floored.tobytes()


def test_render_text_default_font_size_uses_max_on_large_tape():
    """Default font size uses max_font_size when it exceeds the 50px floor."""
    tape = TapeWidth.MM_36
    fitted = max_font_size(tape, 1)
    assert fitted > 50
    default = render_text("Hi", tape)
    explicit = render_text("Hi", tape, font_size=fitted)
    assert default.tobytes() == explicit.tobytes()


@pytest.mark.parametrize("text", ["", "   ", "\n\n"])
def test_render_text_rejects_empty_text(text):
    """Empty or whitespace-only text raises ImagingError."""
    with pytest.raises(ImagingError, match="text"):
        render_text(text, TapeWidth.MM_24)


def test_render_text_rejects_invalid_align():
    """Invalid align raises ImagingError."""
    with pytest.raises(ImagingError, match="align"):
        render_text("Hi", TapeWidth.MM_24, align="justify")


@pytest.mark.parametrize("rotate", [45, 91, 360])
def test_render_text_rejects_invalid_rotate(rotate):
    """Invalid rotation raises ImagingError."""
    with pytest.raises(ImagingError, match="rotation"):
        render_text("Hi", TapeWidth.MM_24, rotate=rotate)


def test_render_text_rejects_negative_margin():
    """Negative margin raises ImagingError."""
    with pytest.raises(ImagingError, match="margin"):
        render_text("Hi", TapeWidth.MM_24, margin=-1)


@pytest.mark.parametrize("font_size", [0, -1])
def test_render_text_rejects_invalid_font_size(font_size):
    """font_size below 1 raises ValueError."""
    with pytest.raises(ValueError, match="font size"):
        render_text("Hi", TapeWidth.MM_24, font_size=font_size)


def test_render_text_rejects_missing_font_path():
    """Missing font_path raises ImagingError."""
    with pytest.raises(ImagingError, match="failed to load font"):
        render_text("Hi", TapeWidth.MM_24, font_path="/nonexistent/font.ttf")


def test_render_text_default_font_renders_ink():
    """Default scalable font renders visible text without a font path."""
    image = render_text("Default", TapeWidth.MM_24)
    assert _ink_pixel_count(image) > 0


def test_render_text_feeds_image_to_raster_without_scaling_error():
    """Rendered text passes through image_to_raster at rotate=0 without distortion."""
    tape = TapeWidth.MM_24
    image = render_text("Raster\nPath", tape, rotate=90)
    lines = image_to_raster(image, tape, rotate=0)
    assert len(lines) == image.width
    for line in lines:
        raster_line(line)
    job = encode_job(tape, lines)
    assert len(job) > len(lines) * RASTER_LINE_BYTES


def _text_to_job(text: str, tape: TapeWidth, **kwargs: object) -> bytes:
    image = render_text(text, tape, **kwargs)
    lines = image_to_raster(image, tape, rotate=0)
    for line in lines:
        raster_line(line)
    return encode_job(tape, lines)


@pytest.mark.parametrize(
    ("label", "kwargs"),
    [
        ("Single", {}),
        ("Line1\nLine2", {}),
        ("Align", {"align": "left"}),
        ("Align", {"align": "right"}),
        ("Sized", {"font_size": 48}),
        ("Turn", {"rotate": 90}),
        ("Turn", {"rotate": 180}),
        ("Turn", {"rotate": 270}),
    ],
)
def test_render_text_end_to_end_feature_matrix(label, kwargs):
    """Text labels across features produce valid raster print jobs."""
    tape = TapeWidth.MM_24
    job = _text_to_job(label, tape, **kwargs)
    assert len(job) > RASTER_LINE_BYTES
