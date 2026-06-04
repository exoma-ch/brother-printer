"""Generate golden PNG fixtures for text rendering regression tests.

Each fixture uses the bundled DejaVuSans.ttf and a fixed font size so output is
identical in the devcontainer and CI.

Run via::

    just gen-text-images
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from brother_printer.protocol.enums import TapeWidth
from brother_printer_text.text import render_text

_ASSETS_DIR = Path(__file__).resolve().parent
_GOLDEN_DIR = _ASSETS_DIR / "golden"
_FONT_PATH = _ASSETS_DIR / "DejaVuSans.ttf"
_FONT_SIZE = 32


@dataclass(frozen=True)
class _FixtureSpec:
    filename: str
    text: str
    tape_width: TapeWidth
    align: str = "center"
    rotate: int = 0


_FIXTURES: tuple[_FixtureSpec, ...] = (
    _FixtureSpec("single_12mm.png", "Hello", TapeWidth.MM_12),
    _FixtureSpec("single_24mm.png", "Hello", TapeWidth.MM_24),
    _FixtureSpec("single_36mm.png", "Hello", TapeWidth.MM_36),
    _FixtureSpec(
        "multiline_24mm.png",
        "Line1\nLine2\nLine3",
        TapeWidth.MM_24,
    ),
    _FixtureSpec(
        "align_left_24mm.png",
        "ABCDEFGH",
        TapeWidth.MM_24,
        align="left",
    ),
    _FixtureSpec(
        "align_right_24mm.png",
        "ABCDEFGH",
        TapeWidth.MM_24,
        align="right",
    ),
    _FixtureSpec("rotate_0_24mm.png", "Rotate", TapeWidth.MM_24, rotate=0),
    _FixtureSpec("rotate_90_24mm.png", "Rotate", TapeWidth.MM_24, rotate=90),
)


def generate_all(output_dir: Path | None = None) -> list[Path]:
    """Render golden text images; return written paths."""
    target_dir = output_dir or _GOLDEN_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for spec in _FIXTURES:
        image = render_text(
            spec.text,
            spec.tape_width,
            font_path=str(_FONT_PATH),
            font_size=_FONT_SIZE,
            align=spec.align,
            rotate=spec.rotate,
        )
        path = target_dir / spec.filename
        image.save(path)
        written.append(path)

    return written


def main() -> None:
    paths = generate_all()
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
