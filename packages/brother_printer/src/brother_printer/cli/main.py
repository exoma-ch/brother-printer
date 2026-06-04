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
    print_strip,
    query_status,
    select_printer,
)
from brother_printer.cli.csv_jobs import load_csv_jobs
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
    "paths",
    nargs=-1,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--tape",
    required=True,
    type=click.Choice(sorted(_TAPE_CHOICES.keys())),
    help="TZe tape width loaded in the printer.",
)
@click.option(
    "--csv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="CSV file listing images to print as one label strip.",
)
@click.option("--auto-cut/--no-cut", default=True, help="Auto-cut after printing.")
@click.option(
    "--half-cut/--no-half-cut", default=False, help="Half-cut peelable labels."
)
@click.option(
    "--strip/--no-strip",
    default=False,
    help="Chain copies or multiple images into one label strip.",
)
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
    help="Rotate label before printing (0/90/180/270 degrees).",
)
@click.option(
    "--margin",
    type=click.IntRange(min=0),
    default=0,
    show_default=True,
    help="White margin in pixels on all sides.",
)
@click.option(
    "--scale",
    is_flag=True,
    default=False,
    help="Resize image height to match tape print area when dimensions differ.",
)
@click.option(
    "--printer",
    "-p",
    default=None,
    help="Printer identifier from discover (default: first found).",
)
def print_cmd(
    paths: tuple[Path, ...],
    tape: str,
    csv: Path | None,
    auto_cut: bool,
    half_cut: bool,
    strip: bool,
    copies: int,
    threshold: int,
    rotate: str,
    margin: int,
    scale: bool,
    printer: str | None,
) -> None:
    """Print PNG or other image files on a connected PT-E920BT."""
    sources = sum(bool(x) for x in (paths, csv is not None))
    if sources != 1:
        if sources > 1:
            click.echo(
                "Provide exactly one of image paths or --csv.",
                err=True,
            )
        else:
            click.echo(
                "Provide at least one image path or --csv.",
                err=True,
            )
        sys.exit(2)

    tape_width = _TAPE_CHOICES[tape]
    print_kwargs = {
        "printer": printer,
        "threshold": threshold,
        "rotate": int(rotate),
        "margin": margin,
        "auto_cut": auto_cut,
        "half_cut": half_cut,
        "scale": scale,
    }

    try:
        if csv is not None:
            written = _print_csv_strip(csv, tape_width, print_kwargs)
        elif len(paths) > 1 or strip:
            written = _print_paths_strip(
                paths, tape_width, copies=copies, **print_kwargs
            )
        else:
            with Image.open(paths[0]) as image:
                written = print_image(
                    image,
                    tape_width,
                    copies=copies,
                    **print_kwargs,
                )
    except ValueError as exc:
        click.echo(str(exc), err=True)
        sys.exit(2)
    except (PrintError, TransportError, ImagingError) as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    click.echo(f"Printed {written} bytes.")


def _print_paths_strip(
    paths: tuple[Path, ...],
    tape_width: TapeWidth,
    *,
    copies: int,
    **print_kwargs: object,
) -> int:
    images: list[Image.Image] = []
    for path in paths:
        with Image.open(path) as image:
            images.append(image.copy())
    return print_strip(images, tape_width, copies=copies, **print_kwargs)


def _print_csv_strip(
    csv_path: Path,
    tape_width: TapeWidth,
    print_kwargs: dict[str, object],
) -> int:
    jobs = load_csv_jobs(csv_path)
    images: list[Image.Image] = []
    for job in jobs:
        with Image.open(job.path) as image:
            for _ in range(job.copies):
                images.append(image.copy())
    return print_strip(images, tape_width, copies=1, **print_kwargs)
