"""Print orchestration for text labels."""

from __future__ import annotations

from brother_ptouch_driver import (
    PrintError,
    discover,
    print_image,
    query_status,
    select_printer,
)
from brother_ptouch_driver.protocol.enums import TapeWidth
from brother_ptouch_label.text import render_text


def detect_tape_width(*, printer: str | None = None) -> TapeWidth:
    """Return the tape width currently loaded in the printer."""
    selected = select_printer(discover(), printer)
    status = query_status(selected)
    if status.media_width is None:
        msg = "No tape loaded; insert a TZe tape and retry"
        raise PrintError(msg)
    return status.media_width


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
    margin_top: int | None = None,
    margin_bottom: int | None = None,
    margin_left: int | None = None,
    margin_right: int | None = None,
    fixed_width: int | None = None,
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
        margin_top=margin_top,
        margin_bottom=margin_bottom,
        margin_left=margin_left,
        margin_right=margin_right,
        fixed_width=fixed_width,
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
