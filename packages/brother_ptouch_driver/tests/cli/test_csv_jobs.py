"""Tests for CSV print job parsing."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from brother_ptouch_driver.cli.csv_jobs import load_csv_jobs


def test_load_csv_jobs_parses_image_and_copies():
    """load_csv_jobs() resolves relative paths and copies counts."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path("a.png").write_bytes(b"png")
        Path("b.png").write_bytes(b"png")
        Path("jobs.csv").write_text(
            "image,copies\na.png,2\nb.png,1\n",
            encoding="utf-8",
        )

        jobs = load_csv_jobs(Path("jobs.csv"))

    assert len(jobs) == 2
    assert jobs[0].path.name == "a.png"
    assert jobs[0].copies == 2
    assert jobs[1].path.name == "b.png"
    assert jobs[1].copies == 1


def test_load_csv_jobs_defaults_copies_to_one():
    """load_csv_jobs() uses copies=1 when the column is omitted."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path("label.png").write_bytes(b"png")
        Path("jobs.csv").write_text("image\nlabel.png\n", encoding="utf-8")

        jobs = load_csv_jobs(Path("jobs.csv"))

    assert jobs[0].copies == 1


@pytest.mark.parametrize(
    ("csv_text", "match"),
    [
        ("copies,foo\nx.png,1\n", "image"),
        ("image,copies\n,2\n", "must not be empty"),
        ("image,copies\nmissing.png,1\n", "not found"),
        ("image,copies\nlabel.png,0\n", "at least 1"),
        ("image,copies\nlabel.png,abc\n", "integer"),
    ],
)
def test_load_csv_jobs_rejects_invalid_rows(csv_text, match):
    """load_csv_jobs() validates headers, paths, and copies values."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        Path("label.png").write_bytes(b"png")
        Path("jobs.csv").write_text(csv_text, encoding="utf-8")

        with pytest.raises(ValueError, match=match):
            load_csv_jobs(Path("jobs.csv"))
