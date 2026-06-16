"""Human-readable CLI output for printer status."""

from __future__ import annotations

from enum import IntEnum

from brother_ptouch_driver import PrinterInfo, PrinterStatus, TapeColor

_PHASE_LABELS: dict[str, str] = {
    "EDITING": "Idle",
    "PRINTING": "Printing",
}


def _format_enum(value: IntEnum | int) -> str:
    """Friendly name for a known enum member, else ``unknown (0xNN)``."""
    if isinstance(value, IntEnum):
        return value.name.replace("_", " ").title()
    return f"unknown (0x{int(value):02x})"


def _format_tape_width(status: PrinterStatus) -> str:
    if status.media_width is None:
        return "No tape"
    return f"{status.media_width.mm:g} mm"


def _format_color(status: PrinterStatus) -> str:
    if status.tape_color == TapeColor.NO_TAPE:
        return "No tape"
    return _format_enum(status.tape_color)


def _format_phase(status: PrinterStatus) -> str:
    if not isinstance(status.phase_type, IntEnum):
        return _format_enum(status.phase_type)
    name = status.phase_type.name
    return _PHASE_LABELS.get(name, name.replace("_", " ").title())


def _format_status_line(status: PrinterStatus) -> str:
    if status.errors:
        return ", ".join(status.errors)
    return "Ready"


def status_has_errors(status: PrinterStatus) -> bool:
    """True when the printer reports error conditions in the status reply."""
    return bool(status.errors)


def render_status(info: PrinterInfo, status: PrinterStatus) -> str:
    """Render a human-readable status block for one printer."""
    header = f"{info.product}  {info.identifier}  (bus {info.bus}, addr {info.address})"
    lines = [
        header,
        f"  Tape:       {_format_tape_width(status)}",
        f"  Color:      {_format_color(status)}",
        f"  Media:      {_format_enum(status.media_type)}",
        f"  Phase:      {_format_phase(status)}",
        f"  Status:     {_format_status_line(status)}",
    ]
    return "\n".join(lines)
