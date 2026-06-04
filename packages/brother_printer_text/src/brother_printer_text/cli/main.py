"""Click CLI entry point for brother-label-text."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from brother_printer import PrintError, TapeWidth, TransportError
from brother_printer.imaging.errors import ImagingError
from brother_printer_text.printing import print_text

_TAPE_CHOICES: dict[str, TapeWidth] = {
    "3.5mm": TapeWidth.MM_3_5,
    "6mm": TapeWidth.MM_6,
    "9mm": TapeWidth.MM_9,
    "12mm": TapeWidth.MM_12,
    "18mm": TapeWidth.MM_18,
    "24mm": TapeWidth.MM_24,
    "36mm": TapeWidth.MM_36,
}


@click.command()
@click.option(
    "--text",
    required=True,
    help="Label text to print (use \\n for multiple lines).",
)
@click.option(
    "--tape",
    required=True,
    type=click.Choice(sorted(_TAPE_CHOICES.keys())),
    help="TZe tape width loaded in the printer.",
)
@click.option(
    "--font",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="TrueType font file (default: built-in scalable font).",
)
@click.option(
    "--font-size",
    type=click.IntRange(min=1),
    default=None,
    help="Font size in pixels (default: auto-fit to tape height).",
)
@click.option(
    "--align",
    type=click.Choice(["left", "center", "right"]),
    default="center",
    show_default=True,
    help="Horizontal alignment for each line of text.",
)
@click.option(
    "--line-spacing",
    type=float,
    default=0.0,
    show_default=True,
    help="Extra spacing between lines as a fraction of line height.",
)
@click.option("--auto-cut/--no-cut", default=True, help="Auto-cut after printing.")
@click.option(
    "--half-cut/--no-half-cut", default=False, help="Half-cut peelable labels."
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
    "--printer",
    "-p",
    default=None,
    help="Printer identifier from discover (default: first found).",
)
@click.version_option(package_name="brother_printer_text")
def main(
    text: str,
    tape: str,
    font: Path | None,
    font_size: int | None,
    align: str,
    line_spacing: float,
    auto_cut: bool,
    half_cut: bool,
    copies: int,
    threshold: int,
    rotate: str,
    margin: int,
    printer: str | None,
) -> None:
    """Print a text label on a connected PT-E920BT."""
    tape_width = _TAPE_CHOICES[tape]
    label_text = text.replace("\\n", "\n")

    try:
        written = print_text(
            label_text,
            tape_width,
            printer=printer,
            copies=copies,
            font_path=str(font) if font is not None else None,
            font_size=font_size,
            align=align,
            line_spacing=line_spacing,
            rotate=int(rotate),
            margin=margin,
            threshold=threshold,
            auto_cut=auto_cut,
            half_cut=half_cut,
        )
    except (PrintError, TransportError, ImagingError) as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    click.echo(f"Printed {written} bytes.")
