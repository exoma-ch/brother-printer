"""Import tests for the v0.1 package skeleton."""

import importlib

import pytest


@pytest.mark.parametrize(
    "name",
    [
        "brother_printer.transport",
        "brother_printer.protocol",
        "brother_printer.imaging",
        "brother_printer.cli",
    ],
)
def test_subpackage_importable_with_docstring(name):
    """Each subpackage must import and declare its responsibility."""
    mod = importlib.import_module(name)
    assert mod.__doc__ and mod.__doc__.strip()
