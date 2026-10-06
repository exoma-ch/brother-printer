"""Environment-tolerant comparison of a render against a committed golden.

Why this exists
---------------
The golden images under ``tests/assets/golden/`` used to be compared byte-for-byte.
That worked only because development and CI ran the same container image, so
both rasterized text with the same Pillow/C-library stack. Since the project
moved to the Nix dev shell (#60) the two diverge by design: devkit's
``setup-devkit-toolchain`` forwards ``UV_PYTHON`` only on a NixOS runner, so a
hosted runner builds the venv on its own system interpreter while a NixOS dev
host uses the Nix store one. Same Pillow, same committed ``DejaVuSans.ttf``, but
glyph advances differ by 1-3 px (and ~8 px at the 48 px default cap), which a
byte-exact assertion can never survive.

Byte-exactness against a font rasterizer is not a portable property, so these
helpers assert the properties the goldens exist to protect instead:

``height``
    Exact. Output height is set by the tape width and the self-laminating band
    confinement, not by glyph advances -- every observed CI divergence was
    width-only. This is what distinguishes a 12 mm render from a 24 mm one and
    what guards the band logic.
``width``
    Within a proportional tolerance. Catches a gross layout change while
    tolerating advance differences.
ink band count
    Exact. The number of horizontal ink runs distinguishes single-line from
    multiline, and 0-degree from 90-degree rotation.
normalized ink geometry
    Coverage, centroid and bounding box as fractions of the image. Scale-free,
    so a few pixels of drift barely move them, while ``align=left`` versus
    ``align=right`` moves the x-centroid by half the image.

Thresholds are calibrated against the committed goldens: the harshest
simulated environment drift (8 px narrower plus a 2 px vertical shift) scores
0.085, while a genuine alignment inversion scores 0.50 and rotation/multiline
changes alter the band count outright.

Refs: #60
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

# Ink is "dark"; renders are 8-bit greyscale with a white background.
_INK_THRESHOLD = 128

# Normalized-geometry tolerance. Calibrated worst legitimate drift is 0.085.
_GEOMETRY_TOL = 0.12

# Width tolerance: proportional, with an absolute floor for small renders.
# The 48 px default-cap render drifts ~7.8%, so 10% leaves headroom.
_WIDTH_TOL_RATIO = 0.10
_WIDTH_TOL_FLOOR_PX = 3


@dataclass(frozen=True)
class _InkGeometry:
    coverage: float
    centroid_x: float
    centroid_y: float
    left: float
    right: float
    top: float
    bottom: float
    bands: int


def _ink_geometry(image: Image.Image) -> _InkGeometry:
    grey = image.convert("L")
    width, height = grey.size
    mask = grey.point(lambda v: 255 if v < _INK_THRESHOLD else 0)
    pixels = list(mask.get_flattened_data())
    count = sum(1 for v in pixels if v)

    if count == 0:
        return _InkGeometry(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)

    centroid_x = sum(i % width for i, v in enumerate(pixels) if v) / count
    centroid_y = sum(i // width for i, v in enumerate(pixels) if v) / count
    left, top, right, bottom = mask.getbbox()

    # Horizontal ink runs: a row with ink whose predecessor had none starts a band.
    rows = [any(pixels[y * width + x] for x in range(width)) for y in range(height)]
    bands = sum(1 for y, inked in enumerate(rows) if inked and not (y and rows[y - 1]))

    return _InkGeometry(
        coverage=count / (width * height),
        centroid_x=centroid_x / width,
        centroid_y=centroid_y / height,
        left=left / width,
        right=right / width,
        top=top / height,
        bottom=bottom / height,
        bands=bands,
    )


def assert_render_close(
    actual: Image.Image,
    expected: Image.Image,
    *,
    label: str = "render",
    width_tol_ratio: float = _WIDTH_TOL_RATIO,
    geometry_tol: float = _GEOMETRY_TOL,
) -> None:
    """Assert ``actual`` matches ``expected`` modulo rasterizer drift.

    Raises AssertionError naming the property that diverged. See the module
    docstring for why this is not a byte-for-byte comparison.
    """
    assert actual.height == expected.height, (
        f"{label}: height {actual.height} != {expected.height}. Output height is "
        f"set by tape width and band confinement, so it must match exactly."
    )

    width_tol = max(_WIDTH_TOL_FLOOR_PX, math.ceil(expected.width * width_tol_ratio))
    width_drift = abs(actual.width - expected.width)
    assert width_drift <= width_tol, (
        f"{label}: width {actual.width} differs from {expected.width} by "
        f"{width_drift}px, over the {width_tol}px tolerance. A few pixels are "
        f"rasterizer drift; this is a layout change. Regenerate with "
        f"`just gen-fixtures-labels` only if the change is intended."
    )

    got, want = _ink_geometry(actual), _ink_geometry(expected)

    assert got.bands == want.bands, (
        f"{label}: {got.bands} horizontal ink band(s), expected {want.bands}. "
        f"Line count or orientation changed."
    )

    for name in (
        "coverage",
        "centroid_x",
        "centroid_y",
        "left",
        "right",
        "top",
        "bottom",
    ):
        drift = abs(getattr(got, name) - getattr(want, name))
        assert drift <= geometry_tol, (
            f"{label}: normalized {name} drifted {drift:.4f} "
            f"({getattr(got, name):.4f} vs {getattr(want, name):.4f}), over the "
            f"{geometry_tol} tolerance. Layout changed, not just rasterization."
        )
