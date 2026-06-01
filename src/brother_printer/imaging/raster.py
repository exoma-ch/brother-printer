"""Image-to-raster pipeline tuned for QR sharpness at 360 dpi.

See docs/vendor/tze-tape-widths.md.
"""

from __future__ import annotations

from PIL import Image

from brother_printer.imaging.errors import ImageScalingError, ImagingError
from brother_printer.protocol.constants import HEAD_PINS, RASTER_LINE_BYTES
from brother_printer.protocol.enums import TapeWidth

_VALID_ROTATIONS = frozenset({0, 90, 180, 270})


def to_monochrome(image: Image.Image, threshold: int = 128) -> Image.Image:
    """Convert any PIL mode to strict 1-bit monochrome (no dithering)."""
    if image.mode == "RGBA":
        background = Image.new("RGBA", image.size, (255, 255, 255, 255))
        flattened = Image.alpha_composite(background, image)
        grayscale = flattened.convert("L")
    elif image.mode == "RGB":
        grayscale = image.convert("L")
    elif image.mode == "L":
        grayscale = image
    elif image.mode == "1":
        return image.copy()
    else:
        grayscale = image.convert("L")

    return grayscale.point(lambda value: 255 if value >= threshold else 0, mode="1")


def apply_rotation(image: Image.Image, degrees: int) -> Image.Image:
    """Rotate image by 0, 90, 180, or 270 degrees."""
    if degrees not in _VALID_ROTATIONS:
        msg = f"rotation must be one of {sorted(_VALID_ROTATIONS)}, got {degrees}"
        raise ImagingError(msg)
    if degrees == 0:
        return image.copy()
    return image.rotate(degrees, expand=True, resample=Image.Resampling.NEAREST)


def apply_margin(image: Image.Image, margin_px: int) -> Image.Image:
    """Pad image with white margin on all sides."""
    if margin_px < 0:
        msg = "margin must be non-negative"
        raise ImagingError(msg)
    if margin_px == 0:
        return image.copy()

    width, height = image.size
    padded = Image.new(image.mode, (width + 2 * margin_px, height + 2 * margin_px), 255)
    padded.paste(image, (margin_px, margin_px))
    return padded


def resize_to_tape_width(
    image: Image.Image,
    tape_width: TapeWidth,
    *,
    allow_distortion: bool = False,
) -> Image.Image:
    """Resize uniformly so image height matches tape print area."""
    width, height = image.size
    if height == 0:
        msg = "image height must be greater than zero"
        raise ImagingError(msg)

    target_height = tape_width.print_area_pins
    factor = target_height / height

    if not allow_distortion:
        if factor <= 0 or factor != int(factor):
            msg = (
                f"image height {height} requires non-integer scale factor "
                f"{factor:.4g} for {target_height}-pin tape; "
                "QR modules would distort"
            )
            raise ImageScalingError(msg)
        scale = int(factor)
    else:
        scale = factor

    new_width = max(1, round(width * scale))
    new_height = target_height
    return image.resize((new_width, new_height), resample=Image.Resampling.NEAREST)


def _set_pin(line: bytearray, pin: int) -> None:
    byte_index = pin // 8
    bit_index = 7 - (pin % 8)
    line[byte_index] |= 1 << bit_index


def pack_raster_lines(image: Image.Image, tape_width: TapeWidth) -> list[bytes]:
    """Pack a 1-bit image into 70-byte raster lines centered on the print head."""
    if image.mode != "1":
        msg = "pack_raster_lines expects mode '1'"
        raise ImagingError(msg)

    width, height = image.size
    print_area = tape_width.print_area_pins
    if height != print_area:
        msg = f"image height {height} must equal print area {print_area} pins"
        raise ImagingError(msg)

    left_pins = tape_width.print_area_left_pins
    if left_pins + print_area > HEAD_PINS:
        msg = "print area exceeds print head width"
        raise ImagingError(msg)

    pixels = image.load()
    assert pixels is not None
    lines: list[bytes] = []
    for column in range(width):
        line = bytearray(RASTER_LINE_BYTES)
        for row in range(height):
            if pixels[column, row] == 0:
                _set_pin(line, left_pins + row)
        lines.append(bytes(line))
    return lines


def image_to_raster(
    image: Image.Image,
    tape_width: TapeWidth,
    *,
    threshold: int = 128,
    rotate: int = 0,
    margin: int = 0,
    allow_distortion: bool = False,
) -> list[bytes]:
    """Convert a PIL image to 70-byte raster lines for the protocol encoder."""
    mono = to_monochrome(image, threshold=threshold)
    mono = apply_rotation(mono, rotate)
    mono = apply_margin(mono, margin)
    mono = resize_to_tape_width(
        mono,
        tape_width,
        allow_distortion=allow_distortion,
    )
    return pack_raster_lines(mono, tape_width)
