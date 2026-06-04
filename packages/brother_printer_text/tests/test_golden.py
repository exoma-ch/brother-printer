"""Golden-image regression tests for render_text.

Committed ONGs under tests/assets/golden/ are compared byte-for-byte against
fresh renders using the bundled DejaVuSans.ttf. When rendering intentionally
changes, regenerate fixtures::

    just gen-text-images
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from PIL import Image

from brother_printer.protocol.enums import TapeWidth
from brother_printer_text.text import render_text

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_GOLDEN_DIR = _ASSETS_DIR / "golden"
_GOLDEN_FONT_SIZE = 32


@dataclass(frozen=True)
class _GoldenCase:
    filename: str
    text: str
    tape_width: TapeWidth
    align: str = "center"
    rotate: int = 0


_GOLDEN_CASES: tuple[_GoldenCase, ...] = (
    _GoldenCase("single_12mm.png", "Hello", TapeWidth.MM_12),
    _GoldenCase("single_24mm.png", "Hello", TapeWidth.MM_24),
    _GoldenCase("single_36mm.png", "Hello", TapeWidth.MM_36),
    _GoldenCase("multiline_24mm.png", "Line1\nLine2\nLine3", TapeWidth.MM_24),
    _GoldenCase("align_left_24mm.png", "ABCDEFGH", TapeWidth.MM_24, align="left"),
    _GoldenCase("align_right_24mm.png", "ABCDEFGH", TapeWidth.MM_24, align="right"),
    _GoldenCase("rotate_0_24mm.png", "Rotate", TapeWidth.MM_24, rotate=0),
    _GoldenCase("rotate_90_24mm.png", "Rotate", TapeWidth.MM_24, rotate=90),
)


@pytest.mark.parametrize("case", _GOLDEN_CASES, ids=lambda c: c.filename)
def test_render_text_matches_golden(case: _GoldenCase, golden_font: Path) -> None:
    """Rendered output matches the committed golden PNG."""
    expected_path = _GOLDEN_DIR / case.filename
    assert expected_path.is_file(), (
        f"missing golden {case.filename}; run: just gen-text-images"
    )

    expected = Image.open(expected_path).convert("L")
    actual = render_text(
        case.text,
        case.tape_width,
        font_path=str(golden_font),
        font_size=_GOLDEN_FONT_SIZE,
        align=case.align,
        rotate=case.rotate,
    )

    assert actual.size == expected.size
    assert actual.tobytes() == expected.tobytes()
