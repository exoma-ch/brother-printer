"""Tests for image-to-raster pipeline tuned for QR sharpness."""

from __future__ import annotations

import pytest
from PIL import Image

from brother_printer.imaging.errors import ImageScalingError, ImagingError
from brother_printer.imaging.raster import (
    apply_margin,
    apply_rotation,
    image_to_raster,
    pack_raster_lines,
    resize_to_tape_width,
    to_monochrome,
)
from brother_printer.protocol.constants import HEAD_PINS, RASTER_LINE_BYTES
from brother_printer.protocol.encoder import encode_job, raster_line
from brother_printer.protocol.enums import TapeWidth


def _checkerboard(
    modules: int,
    module_px: int,
    *,
    mode: str = "L",
) -> Image.Image:
    """Build a square QR-like checkerboard (modules x modules cells)."""
    size = modules * module_px
    image = Image.new(mode, (size, size), 255)
    pixels = image.load()
    assert pixels is not None
    for y in range(size):
        for x in range(size):
            cell_x = x // module_px
            cell_y = y // module_px
            value = 0 if (cell_x + cell_y) % 2 == 0 else 255
            pixels[x, y] = value
    return image


def test_to_monochrome_from_grayscale():
    """Grayscale images convert to strict 1-bit without dithering."""
    image = Image.new("L", (2, 1))
    pixels = image.load()
    assert pixels is not None
    pixels[0, 0] = 50
    pixels[1, 0] = 200

    mono = to_monochrome(image, threshold=128)

    assert mono.mode == "1"
    assert mono.getpixel((0, 0)) == 0
    assert mono.getpixel((1, 0)) == 255


def test_to_monochrome_from_rgba_flattens_alpha():
    """RGBA images flatten onto white before thresholding."""
    image = Image.new("RGBA", (1, 1), (0, 0, 0, 64))

    mono = to_monochrome(image, threshold=128)

    assert mono.mode == "1"
    assert mono.getpixel((0, 0)) == 255


def test_to_monochrome_from_rgb():
    """RGB images convert through grayscale to 1-bit."""
    image = Image.new("RGB", (1, 1), (0, 0, 0))

    mono = to_monochrome(image, threshold=128)

    assert mono.mode == "1"
    assert mono.getpixel((0, 0)) == 0


def test_to_monochrome_threshold_boundary():
    """Pixels below threshold are black; at or above are white."""
    image = Image.new("L", (2, 1))
    pixels = image.load()
    assert pixels is not None
    pixels[0, 0] = 127
    pixels[1, 0] = 128

    mono = to_monochrome(image, threshold=128)

    assert mono.getpixel((0, 0)) == 0
    assert mono.getpixel((1, 0)) == 255


@pytest.mark.parametrize(
    ("degrees", "expected_size"),
    [(0, (3, 2)), (90, (2, 3)), (180, (3, 2)), (270, (2, 3))],
)
def test_apply_rotation(degrees: int, expected_size: tuple[int, int]):
    """Rotation accepts 0/90/180/270 and preserves mode."""
    image = Image.new("1", (3, 2), 255)
    pixels = image.load()
    assert pixels is not None
    pixels[0, 0] = 0

    rotated = apply_rotation(image, degrees)

    assert rotated.mode == "1"
    assert rotated.size == expected_size
    assert 0 in rotated.get_flattened_data()


def test_apply_rotation_rejects_invalid_angle():
    """Invalid rotation angles raise ImagingError."""
    image = Image.new("1", (1, 1), 255)

    with pytest.raises(ImagingError, match="rotation"):
        apply_rotation(image, 45)


def test_apply_margin_adds_white_border():
    """Margin pads with white on all sides."""
    image = Image.new("1", (2, 2), 0)

    padded = apply_margin(image, 1)

    assert padded.size == (4, 4)
    assert padded.getpixel((0, 0)) == 255
    assert padded.getpixel((1, 1)) == 0


def test_apply_margin_rejects_negative():
    """Negative margin values are rejected."""
    image = Image.new("1", (1, 1), 255)

    with pytest.raises(ImagingError, match="margin"):
        apply_margin(image, -1)


def test_resize_to_tape_width_integer_upscale_preserves_modules():
    """Integer nearest-neighbor upscale keeps QR modules sharp."""
    # 20 modules x 4 px = 80 px; 80 -> 320 pins is factor 4 on 24 mm tape.
    image = _checkerboard(modules=20, module_px=4, mode="1")

    resized = resize_to_tape_width(image, TapeWidth.MM_24)

    assert resized.size == (320, 320)
    module_px = 16
    for cell_y in range(20):
        for cell_x in range(20):
            expected = 0 if (cell_x + cell_y) % 2 == 0 else 255
            sample_x = cell_x * module_px + module_px // 2
            sample_y = cell_y * module_px + module_px // 2
            assert resized.getpixel((sample_x, sample_y)) == expected
            corner = (
                cell_x * module_px,
                cell_y * module_px,
            )
            opposite = (
                cell_x * module_px + module_px - 1,
                cell_y * module_px + module_px - 1,
            )
            assert resized.getpixel(corner) == expected
            assert resized.getpixel(opposite) == expected


def test_resize_to_tape_width_rejects_non_integer_factor():
    """Non-integer scale factors raise ImageScalingError by default."""
    image = Image.new("1", (100, 100), 255)

    with pytest.raises(ImageScalingError, match="integer"):
        resize_to_tape_width(image, TapeWidth.MM_24)


def test_resize_to_tape_width_allow_distortion():
    """allow_distortion bypasses integer factor requirement."""
    image = Image.new("1", (100, 100), 255)
    pixels = image.load()
    assert pixels is not None
    pixels[0, 0] = 0

    resized = resize_to_tape_width(image, TapeWidth.MM_24, allow_distortion=True)

    assert resized.size[1] == TapeWidth.MM_24.print_area_pins
    assert resized.getpixel((0, 0)) == 0


def test_pack_raster_lines_emits_70_byte_lines():
    """Each raster line is exactly 70 bytes with centered print area."""
    tape = TapeWidth.MM_24
    image = Image.new("1", (3, tape.print_area_pins), 255)
    pixels = image.load()
    assert pixels is not None
    pixels[0, 0] = 0
    pixels[0, tape.print_area_pins - 1] = 0

    lines = pack_raster_lines(image, tape)

    assert len(lines) == 3
    for line in lines:
        assert len(line) == RASTER_LINE_BYTES

    right_pins = HEAD_PINS - tape.print_area_left_pins - tape.print_area_pins
    right_bytes = right_pins // 8
    right_bit = 7 - (right_pins % 8)
    assert lines[0][right_bytes] & (1 << right_bit)
    bottom_pin = right_pins + tape.print_area_pins - 1
    bottom_byte = bottom_pin // 8
    bottom_bit = 7 - (bottom_pin % 8)
    assert lines[0][bottom_byte] & (1 << bottom_bit)
    assert not any(lines[1])


def test_pack_raster_lines_uses_right_margin_offset():
    """Print area is placed at the right-margin offset per Raster Command Reference §2.3.5."""
    tape = TapeWidth.MM_24
    right_pins = HEAD_PINS - tape.print_area_left_pins - tape.print_area_pins
    assert right_pins == 128
    assert right_pins != tape.print_area_left_pins


def test_pack_raster_lines_requires_print_area_height():
    """pack_raster_lines rejects images whose height differs from print area."""
    image = Image.new("1", (2, 10), 255)

    with pytest.raises(ImagingError, match="height"):
        pack_raster_lines(image, TapeWidth.MM_24)


def test_image_to_raster_end_to_end():
    """image_to_raster output feeds encoder.raster_line() and encode_job()."""
    image = _checkerboard(modules=20, module_px=4, mode="RGB")

    lines = image_to_raster(image, TapeWidth.MM_24, threshold=128, rotate=0, margin=0)

    assert len(lines) == 320
    for line in lines:
        raster_line(line)

    job = encode_job(TapeWidth.MM_24, lines)
    assert len(job) > len(lines) * RASTER_LINE_BYTES


def test_image_to_raster_with_margin_and_rotation():
    """Orchestrator applies margin and rotation before resize/pack."""
    image = Image.new("L", (20, 40), 255)
    pixels = image.load()
    assert pixels is not None
    pixels[0, 0] = 0

    base_lines = image_to_raster(image, TapeWidth.MM_24)
    assert len(base_lines) == 160

    rotated_lines = image_to_raster(image, TapeWidth.MM_24, rotate=90)
    assert len(rotated_lines) == 640

    margined_lines = image_to_raster(image, TapeWidth.MM_24, margin=20)
    assert len(margined_lines) == 240
    assert all(len(line) == RASTER_LINE_BYTES for line in margined_lines)


def _orientation_marker_image(tape: TapeWidth) -> Image.Image:
    """Square image with a black bar on the top edge (rotation marker)."""
    size = tape.print_area_pins
    bar_height = max(2, size // 12)
    image = Image.new("L", (size, size), 255)
    pixels = image.load()
    assert pixels is not None
    for y in range(bar_height):
        for x in range(size):
            pixels[x, y] = 0
    return image


def test_image_to_raster_rotation_changes_raster_bytes():
    """rotate=90 produces different raster output than rotate=0 for asymmetric images."""
    image = _orientation_marker_image(TapeWidth.MM_9)

    lines_0 = image_to_raster(image, TapeWidth.MM_9, rotate=0)
    lines_90 = image_to_raster(image, TapeWidth.MM_9, rotate=90)

    assert lines_0 != lines_90


def test_apply_rotation_four_quarter_turns_restores_image():
    """Four 90-degree rotations return the monochrome image to its original pixels."""
    image = _orientation_marker_image(TapeWidth.MM_9)
    mono = to_monochrome(image)

    rotated = mono
    for _ in range(4):
        rotated = apply_rotation(rotated, 90)

    assert mono.tobytes() == rotated.tobytes()
