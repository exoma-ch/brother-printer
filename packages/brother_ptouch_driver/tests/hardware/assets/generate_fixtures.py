"""Generate PNG fixtures sized for each TZe tape width.

Each label fixture is a text-only canvas whose height equals
``TapeWidth.print_area_pins`` and whose width is the minimum needed to hold the
text. The text states the image height in millimeters and pixels and the
rendered font size (e.g. ``H = 12 mm`` / ``H = 150 px`` / ``FS = 48``) so a
human can verify the correct fixture printed on the loaded tape.

Run via::

    just gen-fixtures-driver
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from brother_ptouch_driver.protocol.enums import TapeWidth

_ASSETS_DIR = Path(__file__).resolve().parent

# Padding around the text, relative to the label height.
_PADDING_DIVISOR = 16
_MIN_FONT_SIZE = 6
_MAX_FONT_SIZE = 48

_LABEL_FILENAMES: dict[TapeWidth, str] = {
    TapeWidth.MM_3_5: "label_3.5mm.png",
    TapeWidth.MM_6: "label_6mm.png",
    TapeWidth.MM_9: "label_9mm.png",
    TapeWidth.MM_12: "label_12mm.png",
    TapeWidth.MM_18: "label_18mm.png",
    TapeWidth.MM_24: "label_24mm.png",
    TapeWidth.MM_36: "label_36mm.png",
}


def _to_strict_1bit(image: Image.Image) -> Image.Image:
    """Convert any mode to strict 1-bit black/white (no dithering)."""
    grayscale = image.convert("L")
    return grayscale.point(lambda value: 255 if value >= 128 else 0, mode="1")


def _label_text(width_mm: float, height_px: int, font_size: int) -> str:
    """Label stating image height in mm and px plus the rendered font size."""
    return f"H = {width_mm:g} mm\nH = {height_px} px\nFS = {font_size}"


def _fit_font_size(draw: ImageDraw.ImageDraw, text: str, *, max_height: int) -> int:
    """Largest default-font size whose multi-line block fits within max_height."""
    upper = max(_MIN_FONT_SIZE, min(_MAX_FONT_SIZE, max_height))
    for size in range(upper, _MIN_FONT_SIZE - 1, -1):
        font = ImageFont.load_default(size=size)
        bbox = draw.multiline_textbbox((0, 0), text, font=font, align="center")
        if bbox[3] - bbox[1] <= max_height:
            return size
    return _MIN_FONT_SIZE


def _render_label(width_mm: float, *, height: int) -> Image.Image:
    """Render a text-only label: image height in mm/px and font size, min width."""
    padding = max(2, height // _PADDING_DIVISOR)
    measure = ImageDraw.Draw(Image.new("L", (1, 1), 255))

    # The block has a fixed line count, so its height does not depend on the
    # font-size digits; fit on a sample, then show the resolved size.
    sample = _label_text(width_mm, height, _MAX_FONT_SIZE)
    font_size = _fit_font_size(measure, sample, max_height=height - 2 * padding)
    text = _label_text(width_mm, height, font_size)
    font = ImageFont.load_default(size=font_size)

    bbox = measure.multiline_textbbox((0, 0), text, font=font, align="center")
    left, top = math.floor(bbox[0]), math.floor(bbox[1])
    text_w = math.ceil(bbox[2]) - left
    text_h = math.ceil(bbox[3]) - top
    width = text_w + 2 * padding

    canvas = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(canvas)
    origin_x = (width - text_w) // 2 - left
    origin_y = (height - text_h) // 2 - top
    draw.multiline_text((origin_x, origin_y), text, fill=0, font=font, align="center")

    return _to_strict_1bit(canvas)


def generate_all(output_dir: Path | None = None) -> list[Path]:
    """Write label fixtures; return output paths."""
    target_dir = output_dir or _ASSETS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for tape_width, filename in _LABEL_FILENAMES.items():
        size = tape_width.print_area_pins
        image = _render_label(tape_width.mm, height=size)
        path = target_dir / filename
        image.save(path)
        written.append(path)

    return written


def main() -> None:
    paths = generate_all()
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
