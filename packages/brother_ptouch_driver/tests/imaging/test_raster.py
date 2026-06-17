"""Tests for image-to-raster pipeline tuned for QR sharpness."""

from __future__ import annotations

import pytest
from PIL import Image

from brother_ptouch_driver.imaging.errors import ImageScalingError, ImagingError
from brother_ptouch_driver.imaging.raster import (
    image_to_raster,
    pack_raster_lines,
    resize_to_tape_width,
    to_monochrome,
)
from brother_ptouch_driver.protocol.constants import HEAD_PINS, RASTER_LINE_BYTES
from brother_ptouch_driver.protocol.encoder import encode_job, raster_line
from brother_ptouch_driver.protocol.enums import TapeWidth


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


def test_to_monochrome_from_mode_1_returns_copy():
    """Mode '1' images pass through as a copy without re-thresholding."""
    image = Image.new("1", (2, 1), 255)
    pixels = image.load()
    assert pixels is not None
    pixels[0, 0] = 0
    pixels[1, 0] = 255

    mono = to_monochrome(image, threshold=128)

    assert mono.mode == "1"
    assert mono is not image
    assert mono.getpixel((0, 0)) == 0
    assert mono.getpixel((1, 0)) == 255


def test_to_monochrome_from_palette_converts_to_1_bit():
    """Palette and other modes convert through grayscale to strict 1-bit."""
    image = Image.new("P", (1, 1))
    image.putpalette([0, 0, 0, 255, 255, 255])
    pixels = image.load()
    assert pixels is not None
    pixels[0, 0] = 0

    mono = to_monochrome(image, threshold=128)

    assert mono.mode == "1"
    assert mono.getpixel((0, 0)) == 0


def test_resize_to_tape_width_strict_rejects_wrong_height():
    """Strict mode rejects images whose height does not match the tape print area."""
    image = Image.new("1", (100, 100), 255)

    with pytest.raises(ImageScalingError, match="must equal print area"):
        resize_to_tape_width(image, TapeWidth.MM_24)


def test_resize_to_tape_width_strict_accepts_exact_height():
    """Strict mode passes through images already at tape print area height."""
    tape = TapeWidth.MM_24
    image = Image.new("1", (50, tape.print_area_pins), 255)

    resized = resize_to_tape_width(image, tape)

    assert resized.size == image.size


def test_resize_to_tape_width_scale_integer_upscale_preserves_modules():
    """Integer nearest-neighbor upscale keeps QR modules sharp when scale=True."""
    # 20 modules x 4 px = 80 px; 80 -> 320 pins is factor 4 on 24 mm tape.
    image = _checkerboard(modules=20, module_px=4, mode="1")

    resized = resize_to_tape_width(image, TapeWidth.MM_24, scale=True)

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


def test_resize_to_tape_width_scale_non_integer_resamples():
    """scale=True resamples when height is not an integer multiple of print area."""
    image = Image.new("1", (100, 100), 255)
    pixels = image.load()
    assert pixels is not None
    pixels[0, 0] = 0

    resized = resize_to_tape_width(image, TapeWidth.MM_24, scale=True)

    assert resized.size[1] == TapeWidth.MM_24.print_area_pins
    assert resized.getpixel((0, 0)) == 0


def test_resize_to_tape_width_scale_integer_downscale():
    """Integer nearest-neighbor downscale shrinks height to print area when scale=True."""
    tape = TapeWidth.MM_3_5
    image = Image.new("1", (100, 96), 255)

    resized = resize_to_tape_width(image, tape, scale=True)

    assert resized.size == (50, tape.print_area_pins)


def test_resize_to_tape_width_scale_non_integer_downscale_resamples():
    """scale=True resamples when downscaling height is not an integer factor."""
    tape = TapeWidth.MM_3_5
    image = Image.new("1", (100, 50), 255)
    pixels = image.load()
    assert pixels is not None
    pixels[0, 0] = 0

    resized = resize_to_tape_width(image, tape, scale=True)

    expected_width = max(1, round(100 * tape.print_area_pins / 50))
    assert resized.size == (expected_width, tape.print_area_pins)
    assert resized.getpixel((0, 0)) == 0


def test_resize_to_tape_width_rejects_zero_height():
    """Zero-height images raise ImagingError before scaling."""
    image = Image.new("1", (5, 0), 255)

    with pytest.raises(ImagingError, match="height must be greater than zero"):
        resize_to_tape_width(image, TapeWidth.MM_3_5, scale=True)


def test_pack_raster_lines_requires_mode_1():
    """pack_raster_lines rejects non-1-bit images."""
    tape = TapeWidth.MM_3_5
    image = Image.new("L", (2, tape.print_area_pins), 255)

    with pytest.raises(ImagingError, match="expects mode '1'"):
        pack_raster_lines(image, tape)


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
    """Print area uses the right-margin offset (hardware-validated on PT-E920BT)."""
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

    lines = image_to_raster(
        image,
        TapeWidth.MM_24,
        threshold=128,
        scale=True,
    )

    assert len(lines) == 320
    for line in lines:
        raster_line(line)

    job = encode_job(TapeWidth.MM_24, lines)
    assert len(job) > len(lines) * RASTER_LINE_BYTES


def test_pack_raster_lines_band_anchors_at_white_strip_edge():
    """A band-height image packs at the white-strip (low-pin) edge of the head."""
    tape = TapeWidth.MM_24
    band = 140  # ~9.8 mm at 360 dpi (self_laminating_band_pins())
    image = Image.new("1", (3, band), 255)
    pixels = image.load()
    assert pixels is not None
    pixels[0, 0] = 0  # top of band
    pixels[0, band - 1] = 0  # bottom of band

    lines = pack_raster_lines(image, tape, effective_height=band)

    right_pins = HEAD_PINS - tape.print_area_left_pins - tape.print_area_pins
    # Row 0 lands at the strip edge; the whole band stays within the print area.
    top_pin = right_pins
    bottom_pin = right_pins + band - 1
    assert lines[0][top_pin // 8] & (1 << (7 - top_pin % 8))
    assert lines[0][bottom_pin // 8] & (1 << (7 - bottom_pin % 8))
    # Nothing is printed in the clear-flap region beyond the band.
    flap_pin = right_pins + band
    assert not (lines[0][flap_pin // 8] & (1 << (7 - flap_pin % 8)))


def test_resize_to_tape_width_effective_height_strict():
    """With a band effective_height, exact-height input is accepted as-is."""
    band = 140
    image = Image.new("1", (4, band), 255)
    result = resize_to_tape_width(image, TapeWidth.MM_24, effective_height=band)
    assert result.size == (4, band)


def test_resize_to_tape_width_effective_height_scales_to_band():
    """scale=True resizes a full-height image down to the band height."""
    image = Image.new("1", (8, TapeWidth.MM_24.print_area_pins), 255)
    result = resize_to_tape_width(
        image, TapeWidth.MM_24, scale=True, effective_height=140
    )
    assert result.size[1] == 140


def test_image_to_raster_band_produces_band_height_lines():
    """End-to-end band path yields lines sized for the band, not the full tape."""
    image = _checkerboard(modules=10, module_px=4, mode="RGB")
    lines = image_to_raster(
        image, TapeWidth.MM_24, threshold=128, scale=True, effective_height=140
    )
    assert all(len(line) == RASTER_LINE_BYTES for line in lines)
    # Confirm every set pin sits inside the white band, never the clear flap.
    right_pins = (
        HEAD_PINS
        - TapeWidth.MM_24.print_area_left_pins
        - TapeWidth.MM_24.print_area_pins
    )
    for line in lines:
        for pin in range(HEAD_PINS):
            if line[pin // 8] & (1 << (7 - pin % 8)):
                assert right_pins <= pin < right_pins + 140
