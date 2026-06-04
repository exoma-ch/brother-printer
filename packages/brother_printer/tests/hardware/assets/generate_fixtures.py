"""Generate PNG fixtures sized for each TZe tape width.

Each QR fixture is a square canvas with side ``TapeWidth.print_area_pins`` so
``image_to_raster()`` uses an integer scale factor of 1 (QR-safe) and remains
rotatable. A solid black bar along the top edge makes rotation visible on
hardware (after ``rotate=90`` the bar appears on a side edge).

Grayscale gradient fixtures exercise ``threshold`` in hardware tests. The shared
``distort_100.png`` (100×100 px) requires a non-integer scale factor for every
supported tape width so ``scale=True`` is meaningful.

Run via::

    just gen-test-images
"""

from __future__ import annotations

from pathlib import Path

import qrcode
from PIL import Image, ImageDraw

from brother_printer.protocol.enums import TapeWidth

_ASSETS_DIR = Path(__file__).resolve().parent

_DISTORT_SIZE = 100
_DISTORT_FILENAME = "distort_100.png"

_TAPE_FILENAMES: dict[TapeWidth, str] = {
    TapeWidth.MM_3_5: "qr_3.5mm.png",
    TapeWidth.MM_6: "qr_6mm.png",
    TapeWidth.MM_9: "qr_9mm.png",
    TapeWidth.MM_12: "qr_12mm.png",
    TapeWidth.MM_18: "qr_18mm.png",
    TapeWidth.MM_24: "qr_24mm.png",
    TapeWidth.MM_36: "qr_36mm.png",
}


def _bar_height(size: int) -> int:
    return max(2, size // 12)


def _render_qr(data: str, *, size: int) -> Image.Image:
    """Render a square fixture with a top orientation bar and centered QR."""
    bar = _bar_height(size)
    qr_size = size - bar
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=0,
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white").convert("L")
    qr_image = qr_image.resize((qr_size, qr_size), resample=Image.Resampling.NEAREST)

    canvas = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, size - 1, bar - 1), fill=0)

    offset_x = (size - qr_size) // 2
    canvas.paste(qr_image, (offset_x, bar))
    return canvas


def _render_grayscale_gradient(*, size: int) -> Image.Image:
    """Vertical grayscale gradient (L mode) for threshold hardware tests."""
    canvas = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(canvas)
    for y in range(size):
        gray = int(255 * y / max(size - 1, 1))
        draw.line([(0, y), (size - 1, y)], fill=gray)
    return canvas


def _render_distort_source(*, size: int = _DISTORT_SIZE) -> Image.Image:
    """Square image whose height yields a non-integer scale to every tape width."""
    canvas = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(canvas)
    inset = max(4, size // 10)
    draw.rectangle((inset, inset, size - inset - 1, size - inset - 1), fill=0)
    return canvas


def generate_all(output_dir: Path | None = None) -> list[Path]:
    """Write QR, grayscale, and distort fixtures; return output paths."""
    target_dir = output_dir or _ASSETS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for tape_width, filename in _TAPE_FILENAMES.items():
        size = tape_width.print_area_pins
        data = f"brother-printer hardware test {tape_width.mm:g}mm"
        image = _render_qr(data, size=size)
        path = target_dir / filename
        image.save(path)
        written.append(path)

        gray_name = filename.replace("qr_", "gray_")
        gray_image = _render_grayscale_gradient(size=size)
        gray_path = target_dir / gray_name
        gray_image.save(gray_path)
        written.append(gray_path)

    distort_path = target_dir / _DISTORT_FILENAME
    _render_distort_source().save(distort_path)
    written.append(distort_path)

    return written


def main() -> None:
    paths = generate_all()
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
