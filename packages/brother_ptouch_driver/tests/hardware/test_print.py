"""Opt-in minimal-tape hardware print matrix for a real PT-E920BT.

Run with::

    just test-hardware packages/brother_ptouch_driver/tests/hardware/test_print.py

Consumes tape. Requires USB passthrough, udev permissions, a loaded TZe tape
matching committed fixtures, and ``BROTHER_PTOUCH_DRIVER_HARDWARE=1``. See TESTING.md
for the print matrix (H1–H2).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from brother_ptouch_driver import TapeMismatchError, print_image, print_strip
from brother_ptouch_driver.imaging.errors import ImageScalingError
from brother_ptouch_driver.protocol.enums import TapeWidth
from brother_ptouch_driver.transport.base import PrinterInfo

from tests.hardware.conftest import (  # noqa: F401
    HARDWARE_PYTESTMARK as pytestmark,
    _ensure_status_readable,
    _wait_for_printer_idle,
)

# Wrong-height image for ImageScalingError guard (height != any tape print area).
_WRONG_HEIGHT_SIZE = 50


def test_print_chained_strip(
    label_fixture_path: Path,
    loaded_tape: TapeWidth,
    printer: PrinterInfo,
) -> None:
    """H1: print_strip() prints a two-page auto-cut chained strip."""
    _wait_for_printer_idle(printer)

    with Image.open(label_fixture_path) as image:
        images = [image.copy() for _ in range(2)]

    _ensure_status_readable(printer)
    written = print_strip(images, loaded_tape, auto_cut=True)

    assert written > 0
    _wait_for_printer_idle(printer)


def test_print_half_cut_strip(
    label_fixture_path: Path,
    laminated_tape: TapeWidth,
    printer: PrinterInfo,
) -> None:
    """H2: print_strip() prints a two-label half-cut strip (laminated tape only)."""
    _wait_for_printer_idle(printer)

    with Image.open(label_fixture_path) as image:
        images = [image.copy() for _ in range(2)]

    _ensure_status_readable(printer)
    written = print_strip(images, laminated_tape, half_cut=True)

    assert written > 0
    _wait_for_printer_idle(printer)


def test_print_wrong_width_raises_tape_mismatch(
    label_fixture_path: Path,
    wrong_tape_width: TapeWidth,
) -> None:
    """Guard: wrong tape width raises TapeMismatchError before any raster write."""
    with Image.open(label_fixture_path) as image:
        with pytest.raises(TapeMismatchError):
            print_image(image.copy(), wrong_tape_width)


def test_print_wrong_height_raises_scaling_error(loaded_tape: TapeWidth) -> None:
    """Guard: wrong image height with scale=False raises ImageScalingError (no tape)."""
    wrong_image = Image.new("1", (_WRONG_HEIGHT_SIZE, _WRONG_HEIGHT_SIZE), 255)
    with pytest.raises(ImageScalingError):
        print_image(wrong_image, loaded_tape, scale=False)
