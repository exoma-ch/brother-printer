"""Generate QR PNG fixtures sized for each TZe tape width.

Each image height equals ``TapeWidth.print_area_pins`` so ``image_to_raster()``
uses an integer scale factor of 1 (QR-safe). Width is at least 60 dots to meet
the vendor minimum print length for TZe tape.

Run via::

    just gen-test-images
"""

from __future__ import annotations

from pathlib import Path

import qrcode
from PIL import Image

from brother_printer.protocol.enums import TapeWidth

_ASSETS_DIR = Path(__file__).resolve().parent
_MIN_RASTER_LINES = 60

_TAPE_FILENAMES: dict[TapeWidth, str] = {
    TapeWidth.MM_3_5: "qr_3.5mm.png",
    TapeWidth.MM_6: "qr_6mm.png",
    TapeWidth.MM_9: "qr_9mm.png",
    TapeWidth.MM_12: "qr_12mm.png",
    TapeWidth.MM_18: "qr_18mm.png",
    TapeWidth.MM_24: "qr_24mm.png",
    TapeWidth.MM_36: "qr_36mm.png",
}


def _render_qr(data: str, *, height: int, width: int) -> Image.Image:
    qr_size = min(height, width)
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

    canvas = Image.new("L", (width, height), 255)
    offset_x = (width - qr_size) // 2
    offset_y = (height - qr_size) // 2
    canvas.paste(qr_image, (offset_x, offset_y))
    return canvas


def generate_all(output_dir: Path | None = None) -> list[Path]:
    """Write one QR PNG per tape width and return the output paths."""
    target_dir = output_dir or _ASSETS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for tape_width, filename in _TAPE_FILENAMES.items():
        height = tape_width.print_area_pins
        width = max(height, _MIN_RASTER_LINES)
        data = f"brother-printer hardware test {tape_width.mm:g}mm"
        image = _render_qr(data, height=height, width=width)
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
