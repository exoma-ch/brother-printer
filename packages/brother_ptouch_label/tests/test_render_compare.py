"""Tests for the golden comparator itself.

A tolerant comparator is only worth having if it still rejects the regressions
the byte-exact one caught. These tests pin both directions: simulated
rasterizer drift must pass, and each class of real layout change must fail.

Refs: #60
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image
from render_compare import assert_render_close

_GOLDEN_DIR = Path(__file__).resolve().parent / "assets" / "golden"


def _golden(name: str) -> Image.Image:
    return Image.open(_GOLDEN_DIR / name).convert("L")


def _drift(image: Image.Image, narrower: int, shift_down: int) -> Image.Image:
    """Simulate rasterizer drift: a narrower canvas with content nudged.

    Stands in for the 1-8 px glyph-advance differences between the Nix dev
    shell and a hosted CI runner (see render_compare's module docstring).
    """
    width, height = image.size
    out = Image.new("L", (max(1, width - narrower), height), 255)
    out.paste(image.crop((narrower, 0, width, height)), (0, shift_down))
    return out


@pytest.mark.parametrize(
    "filename",
    [
        "single_12mm.png",
        "single_24mm.png",
        "single_36mm.png",
        "multiline_24mm.png",
        "align_left_24mm.png",
        "align_right_24mm.png",
        "rotate_0_24mm.png",
        "rotate_90_24mm.png",
        "default_cap_36mm.png",
    ],
)
@pytest.mark.parametrize(
    ("drift_ratio", "shift_down"), [(0.0, 0), (0.02, 0), (0.08, 0), (0.05, 2)]
)
def test_tolerates_rasterizer_drift(
    filename: str, drift_ratio: float, shift_down: int
) -> None:
    """Plausible environment drift must not fail a golden comparison.

    Drift is proportional to width because it accumulates per glyph advance:
    the observed worst case was ~7.8% on a 103 px render. An absolute pixel
    budget would be unrealistically harsh on the narrow rotated goldens.
    """
    golden = _golden(filename)
    narrower = max(1, round(golden.width * drift_ratio)) if drift_ratio else 0
    assert_render_close(_drift(golden, narrower, shift_down), golden, label=filename)


def test_rejects_alignment_inversion() -> None:
    """Left-aligned text must not satisfy the right-aligned golden."""
    with pytest.raises(AssertionError, match="centroid_x"):
        assert_render_close(
            _golden("align_left_24mm.png"), _golden("align_right_24mm.png")
        )


def test_rejects_rotation_change() -> None:
    """A 0-degree render must not satisfy the 90-degree golden."""
    with pytest.raises(AssertionError, match="band|width|height"):
        assert_render_close(_golden("rotate_0_24mm.png"), _golden("rotate_90_24mm.png"))


def test_rejects_line_count_change() -> None:
    """A single-line render must not satisfy the multiline golden."""
    with pytest.raises(AssertionError, match="band"):
        assert_render_close(_golden("single_24mm.png"), _golden("multiline_24mm.png"))


def test_rejects_wrong_tape_width() -> None:
    """A 12 mm render must not satisfy the 24 mm golden: height is exact."""
    with pytest.raises(AssertionError, match="height"):
        assert_render_close(_golden("single_12mm.png"), _golden("single_24mm.png"))


def test_rejects_blank_render() -> None:
    """An empty canvas must not satisfy a golden that has ink."""
    golden = _golden("single_24mm.png")
    blank = Image.new("L", golden.size, 255)
    with pytest.raises(AssertionError, match="band|coverage"):
        assert_render_close(blank, golden)
