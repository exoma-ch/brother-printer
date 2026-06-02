"""Click CLI entry point for brother-printer."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from PIL import Image

from brother_printer import (
    DeviceNotFoundError,
    PrintError,
    TapeWidth,
    TransportError,
    discover_printers,
    print_image,
    query_status,
    select_printer,
)
from brother_printer.cli.render import render_status, status_has_errors
from brother_printer.imaging.errors import ImagingError

_TAPE_CHOICES: dict[str, TapeWidth] = {
    "3.5mm": TapeWidth.MM_3_5,
    "6mm": TapeWidth.MM_6,
    "9mm": TapeWidth.MM_9,
    "12mm": TapeWidth.MM_12,
    "18mm": TapeWidth.MM_18,
    "24mm": TapeWidth.MM_24,
    "36mm": TapeWidth.MM_36,
}


@click.group()
@click.version_option(package_name="brother_printer")
def main() -> None:
    """Brother PT-E920BT label printer CLI."""


@main.group("info")
def info_group() -> None:
    """Reference information (no printer required)."""


@info_group.command("tapes")
def info_tapes_cmd() -> None:
    """List supported TZe tape widths and printable pixel widths at 360 dpi."""
    for width in TapeWidth:
        click.echo(f"{width.mm:g} mm\t{width.print_area_pins} px")


@main.command("discover")
@click.option(
    "--status",
    "-s",
    is_flag=True,
    help="Query live status for each discovered printer.",
)
def discover_cmd(status: bool) -> None:
    """List connected Brother PT-E920BT printers on USB."""
    try:
        printers = discover_printers()
    except TransportError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    if not printers:
        click.echo("No Brother PT-E920BT printers found.", err=True)
        sys.exit(1)

    if not status:
        for printer in printers:
            click.echo(
                f"{printer.identifier}\t{printer.product}\t"
                f"{printer.bus}:{printer.address}"
            )
        return

    had_errors = False
    for index, printer in enumerate(printers):
        if index > 0:
            click.echo()
        try:
            printer_status = query_status(printer)
        except TransportError as exc:
            click.echo(
                f"{printer.product}  {printer.identifier}  "
                f"(bus {printer.bus}, addr {printer.address})"
            )
            click.echo(f"  Status:     {exc}", err=True)
            had_errors = True
            continue

        click.echo(render_status(printer, printer_status))
        if status_has_errors(printer_status):
            had_errors = True

    if had_errors:
        sys.exit(1)


@main.command("status")
@click.option(
    "--printer",
    "-p",
    default=None,
    help="Printer identifier from discover (default: first found).",
)
def status_cmd(printer: str | None) -> None:
    """Show live status for one connected PT-E920BT."""
    try:
        printers = discover_printers()
        selected = select_printer(printers, printer)
        printer_status = query_status(selected)
    except (TransportError, DeviceNotFoundError) as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    click.echo(render_status(selected, printer_status))
    if status_has_errors(printer_status):
        sys.exit(1)


@main.command("print")
@click.argument(
    "path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--tape",
    required=True,
    type=click.Choice(sorted(_TAPE_CHOICES.keys())),
    help="TZe tape width loaded in the printer.",
)
@click.option("--auto-cut/--no-cut", default=True, help="Auto-cut after printing.")
@click.option("--copies", type=click.IntRange(min=1), default=1, show_default=True)
@click.option(
    "--threshold",
    type=click.IntRange(0, 255),
    default=128,
    show_default=True,
    help="Monochrome threshold (0-255).",
)
@click.option(
    "--rotate",
    type=click.Choice(["0", "90", "180", "270"]),
    default="0",
    show_default=True,
    help="Rotate image before printing.",
)
@click.option(
    "--margin",
    type=click.IntRange(min=0),
    default=0,
    show_default=True,
    help="White margin in pixels on all sides.",
)
@click.option(
    "--printer",
    "-p",
    default=None,
    help="Printer identifier from discover (default: first found).",
)
def print_cmd(
    path: Path,
    tape: str,
    auto_cut: bool,
    copies: int,
    threshold: int,
    rotate: str,
    margin: int,
    printer: str | None,
) -> None:
    """Print an image file on a connected PT-E920BT."""
    tape_width = _TAPE_CHOICES[tape]
    try:
        with Image.open(path) as image:
            written = print_image(
                image,
                tape_width,
                printer=printer,
                copies=copies,
                threshold=threshold,
                rotate=int(rotate),
                margin=margin,
                auto_cut=auto_cut,
            )
    except (PrintError, TransportError, ImagingError) as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    click.echo(f"Printed {written} bytes.")
