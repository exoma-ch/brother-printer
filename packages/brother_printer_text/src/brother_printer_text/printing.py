"""Print orchestration for text labels."""

from __future__ import annotations

from brother_printer import print_image
from brother_printer.protocol.enums import TapeWidth
from brother_printer_text.text import render_text


def print_text(
    text: str,
    tape_width: TapeWidth,
    *,
    printer: str | None = None,
    copies: int = 1,
    font_path: str | None = None,
    font_size: int | None = None,
    align: str = "center",
    line_spacing: float = 0.0,
    rotate: int = 0,
    margin: int = 0,
    threshold: int = 128,
    auto_cut: bool = True,
    half_cut: bool = False,
) -> int:
    """Print a text label on a connected PT-E920BT."""
    image = render_text(
        text,
        tape_width,
        font_path=font_path,
        font_size=font_size,
        align=align,
        line_spacing=line_spacing,
        rotate=rotate,
        margin=margin,
    )
    return print_image(
        image,
        tape_width,
        printer=printer,
        copies=copies,
        threshold=threshold,
        rotate=0,
        margin=0,
        auto_cut=auto_cut,
        half_cut=half_cut,
        scale=False,
    )
