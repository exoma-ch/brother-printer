"""Opt-in minimal-tape hardware print matrix for a real PT-E920BT.

Run with::

    just test-hardware packages/brother_printer/tests/hardware/test_print.py

Consumes tape. Requires USB passthrough, udev permissions, a loaded TZe tape
matching committed fixtures, and ``BROTHER_PRINTER_HARDWARE=1``. See TESTING.md
for the print matrix (P0–P4).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from brother_printer import print_strip
from brother_printer.imaging.raster import image_to_raster
from brother_printer_text.text import render_text
from brother_printer.protocol import (
    RASTER_LINE_BYTES,
    STATUS_REPLY_SIZE,
    decode_status,
    encode_job,
    encode_strip_job,
    status_request,
)
from brother_printer.protocol.enums import TapeWidth
from brother_printer.transport import UsbTransport, discover
from brother_printer.transport.base import PrinterInfo

from tests.hardware.conftest import (  # noqa: F401
    HARDWARE_PYTESTMARK as pytestmark,
    PRINTER_REQUIRED_MSG,
    STATUS_READ_TIMEOUT_MS,
    _ensure_status_readable,
    _wait_for_printer_idle,
)

# At least 57 raster lines (4 mm) per vendor minimum print length for TZe tape.
_PRINT_LINE_COUNT = 60
_BLACK_LINE = b"\xff" * RASTER_LINE_BYTES

# High threshold turns the top of the grayscale gradient white on hardware.
_THRESHOLD_HIGH = 200


def test_print_raw_label() -> None:
    """P0: encode_job() over USB prints a short solid-black label (low-level path)."""
    printers = discover()
    assert printers, PRINTER_REQUIRED_MSG

    printer = printers[0]
    with UsbTransport(printer) as transport:
        transport.write(status_request())
        reply = transport.read_exact(
            STATUS_REPLY_SIZE, timeout_ms=STATUS_READ_TIMEOUT_MS
        )
        status = decode_status(reply)

        if status.media_width is None:
            pytest.skip("No tape width reported; load a TZe tape to run print test")

        if status.errors:
            pytest.skip("Printer reported errors: " + ", ".join(status.errors))

        raster_lines = [_BLACK_LINE] * _PRINT_LINE_COUNT
        job = encode_job(status.media_width, raster_lines, no_chain=True)
        written = transport.write(job)

    assert written == len(job)
    _wait_for_printer_idle(printer)


def test_print_visual_variations_strip(
    fixture_path: Path,
    gray_fixture_path: Path,
    distort_fixture_path: Path,
    loaded_tape: TapeWidth,
    printer: PrinterInfo,
) -> None:
    """P1: one chained strip via encode_strip_job (no per-page eject feed)."""
    _wait_for_printer_idle(printer)

    cases: list[tuple[Path, dict[str, Any]]] = [
        (fixture_path, {}),
        (fixture_path, {"rotate": 90}),
        (fixture_path, {"rotate": 180}),
        (fixture_path, {"rotate": 270}),
        (gray_fixture_path, {"threshold": _THRESHOLD_HIGH}),
        (distort_fixture_path, {"scale": True}),
    ]

    pages: list[list[bytes]] = []
    for path, kwargs in cases:
        with Image.open(path) as image:
            pages.append(image_to_raster(image.copy(), loaded_tape, **kwargs))

    job = encode_strip_job(loaded_tape, pages, auto_cut=True)

    _ensure_status_readable(printer)
    with UsbTransport(printer) as transport:
        transport.write(status_request())
        reply = transport.read_exact(
            STATUS_REPLY_SIZE, timeout_ms=STATUS_READ_TIMEOUT_MS
        )
        status = decode_status(reply)

        if status.media_width is None:
            pytest.skip("No tape width reported; load a TZe tape to run print test")

        if status.errors:
            pytest.skip("Printer reported errors: " + ", ".join(status.errors))

        if status.media_width != loaded_tape:
            pytest.skip(
                f"Loaded tape is {status.media_width.mm:g} mm but "
                f"{loaded_tape.mm:g} mm fixture was selected"
            )

        written = transport.write(job)

    assert written == len(job)
    _wait_for_printer_idle(printer)


def test_print_half_cut_strip(
    fixture_path: Path,
    laminated_tape: TapeWidth,
    printer: PrinterInfo,
) -> None:
    """P2: print_strip() prints a two-label half-cut strip (laminated tape only)."""
    _wait_for_printer_idle(printer)

    with Image.open(fixture_path) as image:
        images = [image.copy() for _ in range(2)]

    _ensure_status_readable(printer)
    written = print_strip(images, laminated_tape, half_cut=True)

    assert written > 0
    _wait_for_printer_idle(printer)


def test_print_full_cut_strip_copies(
    fixture_path: Path,
    loaded_tape: TapeWidth,
    printer: PrinterInfo,
) -> None:
    """P3: print_strip(copies=2) prints two full-cut labels in one chained job."""
    _wait_for_printer_idle(printer)

    _ensure_status_readable(printer)
    with Image.open(fixture_path) as image:
        written = print_strip([image.copy()], loaded_tape, copies=2)

    assert written > 0
    _wait_for_printer_idle(printer)


def test_print_text_feature_matrix(
    loaded_tape: TapeWidth,
    printer: PrinterInfo,
) -> None:
    """P4: print_strip() prints text labels (auto-fit, multi-line, size, rotation)."""
    _wait_for_printer_idle(printer)

    cases: list[tuple[str, dict[str, Any]]] = [
        ("AUTO", {}),
        ("Line1\nLine2", {"align": "left"}),
        ("SIZE", {"font_size": 32}),
        ("TURN", {"rotate": 90}),
    ]
    images = [render_text(text, loaded_tape, **kwargs) for text, kwargs in cases]

    _ensure_status_readable(printer)
    written = print_strip(images, loaded_tape, auto_cut=True)

    assert written > 0
    _wait_for_printer_idle(printer)
