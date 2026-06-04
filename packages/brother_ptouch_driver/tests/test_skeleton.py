"""Import tests for the v0.1 package skeleton."""

import importlib

import brother_ptouch_driver
import pytest


def test_version():
    """The root package exposes the project version."""
    assert brother_ptouch_driver.__version__ == "0.1.0"


@pytest.mark.parametrize(
    "name",
    [
        "brother_ptouch_driver.transport",
        "brother_ptouch_driver.protocol",
        "brother_ptouch_driver.imaging",
        "brother_ptouch_driver.cli",
    ],
)
def test_subpackage_importable_with_docstring(name):
    """Each subpackage must import and declare its responsibility."""
    mod = importlib.import_module(name)
    assert mod.__doc__ and mod.__doc__.strip()
