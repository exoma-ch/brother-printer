"""Example tests for brother_printer."""


def test_example():
    """Example test that always passes."""
    assert True


def test_import():
    """Test that the package can be imported."""
    import brother_printer  # noqa: F401 - renamed to project name by init-workspace.sh

    assert brother_printer.__version__ == "0.1.0"
