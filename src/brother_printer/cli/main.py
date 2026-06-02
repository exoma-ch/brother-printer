"""Click CLI entry point for brother-printer."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from PIL import Image

from brother_printer import PrintError, TapeWidth, print_image
from brother_printer.imaging.errors import ImagingError
from brother_printer.transport import discover
from brother_printer.transport.errors import TransportError

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


@main.command("discover")
def discover_cmd() -> None:
    """List connected Brother PT-E920BT printers on USB."""
    try:
        printers = discover()
    except TransportError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    if not printers:
        click.echo("No Brother PT-E920BT printers found.", err=True)
        sys.exit(1)

    for printer in printers:
        click.echo(
            f"{printer.identifier}\t{printer.product}\t{printer.bus}:{printer.address}"
        )


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
