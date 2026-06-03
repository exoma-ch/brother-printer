"""High-level print orchestration for Brother PT-E920BT."""

from __future__ import annotations

from PIL import Image

from brother_printer.imaging.raster import image_to_raster
from brother_printer.protocol.constants import STATUS_REPLY_SIZE
from brother_printer.protocol.decoder import PrinterStatus, decode_status
from brother_printer.protocol.encoder import (
    encode_job,
    encode_strip_job,
    status_request,
)
from brother_printer.protocol.enums import MediaType, TapeWidth
from brother_printer.transport import UsbTransport, discover
from brother_printer.transport.base import PrinterInfo, Transport
from brother_printer.transport.errors import DeviceNotFoundError


class PrintError(Exception):
    """Base exception for print orchestration failures."""


class TapeMismatchError(PrintError):
    """Requested tape width does not match the loaded tape."""


class PrinterNotReadyError(PrintError):
    """Printer is not ready to print (errors or no tape loaded)."""


class HalfCutNotSupportedError(PrintError):
    """Half-cut requested on tape that does not support it (non-laminated)."""


def select_printer(printers: list[PrinterInfo], identifier: str | None) -> PrinterInfo:
    if not printers:
        raise DeviceNotFoundError("No Brother PT-E920BT printers found")

    if identifier is None:
        return printers[0]

    for printer in printers:
        if printer.identifier == identifier:
            return printer

    msg = f"No printer found for identifier {identifier!r}"
    raise DeviceNotFoundError(msg)


def _read_status(transport: Transport, *, timeout_ms: int = 5000) -> PrinterStatus:
    transport.write(status_request())
    reply = transport.read_exact(STATUS_REPLY_SIZE, timeout_ms=timeout_ms)
    return decode_status(reply)


def query_status(
    printer: PrinterInfo,
    *,
    timeout_ms: int = 5000,
) -> PrinterStatus:
    """Query live printer status over USB (ESC i S status reply)."""
    with UsbTransport(printer) as transport:
        return _read_status(transport, timeout_ms=timeout_ms)


def _validate_status(
    status: PrinterStatus,
    tape_width: TapeWidth,
    *,
    half_cut: bool = False,
) -> None:
    if status.errors:
        msg = "Printer reported errors: " + ", ".join(status.errors)
        raise PrinterNotReadyError(msg)

    if status.media_width is None:
        raise PrinterNotReadyError("No tape loaded; insert a TZe tape and retry")

    if status.media_width != tape_width:
        msg = (
            f"Loaded tape is {status.media_width.mm:g} mm but "
            f"{tape_width.mm:g} mm was requested"
        )
        raise TapeMismatchError(msg)

    if half_cut and status.media_type != MediaType.LAMINATED:
        media_label = status.media_type.name.replace("_", " ").lower()
        msg = (
            f"Half-cut requires laminated tape, but loaded media is {media_label}. "
            "See docs/vendor/tze-tape-widths.md (half-cut support)."
        )
        raise HalfCutNotSupportedError(msg)


def print_image(
    image: Image.Image,
    tape_width: TapeWidth,
    *,
    printer: str | None = None,
    copies: int = 1,
    threshold: int = 128,
    rotate: int = 0,
    margin: int = 0,
    auto_cut: bool = True,
    half_cut: bool = False,
    allow_distortion: bool = False,
) -> int:
    """Print a PIL image on a connected PT-E920BT.

    Half-cut requires laminated tape; see docs/vendor/tze-tape-widths.md.
    """
    selected = select_printer(discover(), printer)

    with UsbTransport(selected) as transport:
        status = _read_status(transport)
        _validate_status(status, tape_width, half_cut=half_cut)

        raster_lines = image_to_raster(
            image,
            tape_width,
            threshold=threshold,
            rotate=rotate,
            margin=margin,
            allow_distortion=allow_distortion,
        )
        job = encode_job(
            tape_width,
            raster_lines,
            auto_cut=auto_cut,
            half_cut=half_cut,
        )

        written = 0
        for _ in range(copies):
            written += transport.write(job)
        return written


def print_strip(
    images: list[Image.Image],
    tape_width: TapeWidth,
    *,
    printer: str | None = None,
    copies: int = 1,
    threshold: int = 128,
    rotate: int = 0,
    margin: int = 0,
    auto_cut: bool = True,
    half_cut: bool = False,
    allow_distortion: bool = False,
) -> int:
    """Print a chained strip of labels in one multi-page job.

    Half-cut requires laminated tape; see docs/vendor/tze-tape-widths.md.
    """
    if not images:
        msg = "images must contain at least one label"
        raise ValueError(msg)

    selected = select_printer(discover(), printer)

    with UsbTransport(selected) as transport:
        status = _read_status(transport)
        _validate_status(status, tape_width, half_cut=half_cut)

        raster_kwargs = {
            "threshold": threshold,
            "rotate": rotate,
            "margin": margin,
            "allow_distortion": allow_distortion,
        }
        pages: list[list[bytes]] = []
        for image in images:
            raster_lines = image_to_raster(image, tape_width, **raster_kwargs)
            for _ in range(copies):
                pages.append(raster_lines)

        job = encode_strip_job(
            tape_width,
            pages,
            auto_cut=auto_cut,
            half_cut=half_cut,
        )
        return transport.write(job)
