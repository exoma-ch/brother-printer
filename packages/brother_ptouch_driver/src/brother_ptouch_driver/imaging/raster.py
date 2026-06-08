"""Image-to-raster pipeline tuned for QR sharpness at 360 dpi.

See docs/vendor/tze-tape-widths.md.
"""

from __future__ import annotations

from PIL import Image

from brother_ptouch_driver.imaging.errors import ImageScalingError, ImagingError
from brother_ptouch_driver.protocol.constants import HEAD_PINS, RASTER_LINE_BYTES
from brother_ptouch_driver.protocol.enums import TapeWidth


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


def resize_to_tape_width(
    image: Image.Image,
    tape_width: TapeWidth,
    *,
    scale: bool = False,
) -> Image.Image:
    """Resize uniformly so image height matches tape print area.

    When scale is False (default), image height must already equal the tape print area.
    When scale is True, integer up/downscale uses nearest-neighbor; non-integer factors
    resample to the target height (may distort QR modules).
    """
    width, height = image.size
    if height == 0:
        msg = "image height must be greater than zero"
        raise ImagingError(msg)

    target_height = tape_width.print_area_pins
    if height == target_height:
        return image.copy()

    if not scale:
        msg = (
            f"image height {height} must equal print area {target_height} pins; "
            "pass scale=True to resize"
        )
        raise ImageScalingError(msg)

    if height < target_height:
        if target_height % height != 0:
            new_width = max(1, round(width * (target_height / height)))
            return image.resize(
                (new_width, target_height),
                resample=Image.Resampling.NEAREST,
            )
        factor = target_height // height
        new_width = width * factor
        return image.resize(
            (new_width, target_height),
            resample=Image.Resampling.NEAREST,
        )

    if height % target_height != 0:
        new_width = max(1, round(width * (target_height / height)))
        return image.resize(
            (new_width, target_height),
            resample=Image.Resampling.NEAREST,
        )
    factor = height // target_height
    new_width = max(1, width // factor)
    return image.resize(
        (new_width, target_height),
        resample=Image.Resampling.NEAREST,
    )


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
    right_pins = HEAD_PINS - left_pins - print_area
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
                # Right-margin offset per Raster Command Reference §2.3.5; hardware-validated.
                _set_pin(line, right_pins + row)
        lines.append(bytes(line))
    return lines


def image_to_raster(
    image: Image.Image,
    tape_width: TapeWidth,
    *,
    threshold: int = 128,
    scale: bool = False,
) -> list[bytes]:
    """Convert a PIL image to 70-byte raster lines for the protocol encoder."""
    mono = to_monochrome(image, threshold=threshold)
    mono = resize_to_tape_width(mono, tape_width, scale=scale)
    return pack_raster_lines(mono, tape_width)
