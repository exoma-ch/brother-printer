"""Tests for text rendering and max font size helpers."""

from __future__ import annotations

import pytest
from PIL import Image, ImageDraw, ImageFont

from brother_printer.imaging.text import max_font_size
from brother_printer.protocol.enums import TapeWidth

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
