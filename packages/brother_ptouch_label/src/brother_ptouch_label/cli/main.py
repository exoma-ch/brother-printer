"""Click CLI entry point for brother-ptouch-label."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from brother_ptouch_driver import PrintError, TapeWidth, TransportError
from brother_ptouch_driver.imaging.errors import ImagingError
from brother_ptouch_label.printing import detect_tape_width, print_text
from brother_ptouch_label.text import render_text

_TAPE_CHOICES: dict[str, TapeWidth] = {
    "3.5mm": TapeWidth.MM_3_5,
    "6mm": TapeWidth.MM_6,
    "9mm": TapeWidth.MM_9,
    "12mm": TapeWidth.MM_12,
    "18mm": TapeWidth.MM_18,
    "24mm": TapeWidth.MM_24,
    "36mm": TapeWidth.MM_36,
}


def _resolve_tape(tape: str | None, *, printer: str | None) -> TapeWidth:
    if tape is not None:
        return _TAPE_CHOICES[tape]
    return detect_tape_width(printer=printer)


def _resolve_margins(
    margin: int,
    margin_top: int | None,
    margin_bottom: int | None,
    margin_left: int | None,
    margin_right: int | None,
) -> dict[str, int | None]:
    return {
        "margin": margin,
        "margin_top": margin_top,
        "margin_bottom": margin_bottom,
        "margin_left": margin_left,
        "margin_right": margin_right,
    }


@click.command()
@click.argument("text")
@click.option(
    "--tape",
    default=None,
    type=click.Choice(sorted(_TAPE_CHOICES.keys())),
    help="TZe tape width (default: read from printer).",
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
    help="Font size in pixels (default: largest fitting size, capped at 48px).",
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
    "--rotate/--no-rotate",
    default=False,
    show_default=True,
    help="Rotate label 90° (text across the tape).",
)
@click.option(
    "--margin",
    type=click.IntRange(min=0),
    default=0,
    show_default=True,
    help="White margin in pixels on all sides (overridden per edge).",
)
@click.option("--margin-top", type=click.IntRange(min=0), default=None)
@click.option("--margin-bottom", type=click.IntRange(min=0), default=None)
@click.option("--margin-left", type=click.IntRange(min=0), default=None)
@click.option("--margin-right", type=click.IntRange(min=0), default=None)
@click.option(
    "--width",
    "fixed_width",
    type=click.IntRange(min=1),
    default=None,
    help="Fixed label width in pixels along the feed axis.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Write rendered PNG instead of printing.",
)
@click.option(
    "--printer",
    "-p",
    default=None,
    help="Printer identifier from discover (default: first found).",
)
@click.version_option(package_name="brother_ptouch_label")
def main(
    text: str,
    tape: str | None,
    font: Path | None,
    font_size: int | None,
    align: str,
    line_spacing: float,
    auto_cut: bool,
    half_cut: bool,
    copies: int,
    threshold: int,
    rotate: bool,
    margin: int,
    margin_top: int | None,
    margin_bottom: int | None,
    margin_left: int | None,
    margin_right: int | None,
    fixed_width: int | None,
    output: Path | None,
    printer: str | None,
) -> None:
    """Print a text label on a connected PT-E920BT.

    TEXT may span multiple lines. Pass a literal "\\n" sequence to insert a
    line break (for example "Line 1\\nLine 2"), or supply an actual newline
    via your shell (such as a quoted argument that spans several lines). Use
    --align and --line-spacing to control how the lines are laid out.
    """
    label_text = text.replace("\\n", "\n")
    margin_kwargs = _resolve_margins(
        margin,
        margin_top,
        margin_bottom,
        margin_left,
        margin_right,
    )
    render_kwargs = {
        "font_path": str(font) if font is not None else None,
        "font_size": font_size,
        "align": align,
        "line_spacing": line_spacing,
        "rotate": 90 if rotate else 0,
        "fixed_width": fixed_width,
        **margin_kwargs,
    }

    try:
        tape_width = _resolve_tape(tape, printer=printer)
    except (PrintError, TransportError) as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    try:
        if output is not None:
            image = render_text(label_text, tape_width, **render_kwargs)
            image.save(output)
            click.echo(f"Wrote {output}.")
            return

        written = print_text(
            label_text,
            tape_width,
            printer=printer,
            copies=copies,
            threshold=threshold,
            auto_cut=auto_cut,
            half_cut=half_cut,
            **render_kwargs,
        )
    except (PrintError, TransportError, ImagingError) as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    click.echo(f"Printed {written} bytes.")
