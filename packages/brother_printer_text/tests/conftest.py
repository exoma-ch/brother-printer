"""Shared fixtures for brother_printer_text tests."""

from __future__ import annotations

from pathlib import Path

import pytest

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
GOLDEN_FONT = _ASSETS_DIR / "DejaVuSans.ttf"
GOLDEN_DIR = _ASSETS_DIR / "golden"

# Fixed size for deterministic golden renders (independent of auto-fit).
GOLDEN_FONT_SIZE = 32


@pytest.fixture
def golden_font() -> Path:
    """Path to the bundled DejaVuSans.ttf used for golden image tests."""
    return GOLDEN_FONT
