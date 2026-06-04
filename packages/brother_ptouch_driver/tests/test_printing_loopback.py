"""End-to-end print_image test driven through LoopbackTransport (issue #9).

Unlike test_printing.py, this exercises the real imaging -> encoder -> transport
path with no hardware and no mocking of encode/raster/decode. The captured job
bytes are compared against a committed golden so the full byte stream stays
stable across refactors. Regenerate the golden after an intentional protocol or
imaging change with: UPDATE_GOLDEN=1 just test
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from brother_ptouch_driver import print_image
from brother_ptouch_driver.protocol.encoder import status_request
from brother_ptouch_driver.protocol.enums import TapeWidth
from brother_ptouch_driver.transport import LoopbackTransport
from brother_ptouch_driver.transport.base import PrinterInfo

_GOLDEN = Path(__file__).parent / "golden" / "print_image_24mm.bin"
_STATUS_REPLY = Path(__file__).parent / "protocol" / "golden" / "status_ready_24mm.bin"


def _sample_printer() -> PrinterInfo:
    return PrinterInfo(
        vendor_id=0x04F9,
        product_id=0x20C7,
        serial="000123456789",
        product="PT-E920BT",
        bus=1,
        address=5,
    )


def _checkerboard_24mm() -> Image.Image:
    """Deterministic image whose height matches the 24 mm print area (320 px)."""
    height = TapeWidth.MM_24.print_area_pins
    image = Image.new("L", (5, height), 255)
    pixels = image.load()
    assert pixels is not None
    for x in range(image.width):
        for y in range(height):
            pixels[x, y] = 0 if (x + y) % 2 == 0 else 255
    return image


def test_print_image_end_to_end_through_loopback():
    """print_image() drives the real pipeline; captured job matches the golden."""
    loopback = LoopbackTransport(replies=[_STATUS_REPLY.read_bytes()])

    with (
        patch(
            "brother_ptouch_driver.printing.discover",
            return_value=[_sample_printer()],
        ),
        patch(
            "brother_ptouch_driver.printing.UsbTransport",
            return_value=loopback,
        ),
    ):
        written = print_image(_checkerboard_24mm(), TapeWidth.MM_24)

    # print_image writes the status request first, then the encoded job.
    prefix = status_request()
    captured = bytes(loopback.written)
    assert captured.startswith(prefix)
    job = captured[len(prefix) :]

    if os.environ.get("UPDATE_GOLDEN"):
        _GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        _GOLDEN.write_bytes(job)

    assert job == _GOLDEN.read_bytes()
    assert written == len(job)
    assert loopback.close_count == 1
