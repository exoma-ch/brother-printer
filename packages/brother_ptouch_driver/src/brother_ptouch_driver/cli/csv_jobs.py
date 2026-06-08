"""CSV job list parsing for batch label printing."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CsvPrintJob:
    """One label entry from a CSV print list."""

    path: Path
    copies: int = 1


def load_csv_jobs(csv_path: Path) -> list[CsvPrintJob]:
    """Load print jobs from a CSV file with ``image`` and optional ``copies`` columns."""
    base_dir = csv_path.parent
    jobs: list[CsvPrintJob] = []

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "image" not in reader.fieldnames:
            msg = "CSV must include a header row with an 'image' column"
            raise ValueError(msg)

        for row_number, row in enumerate(reader, start=2):
            image_value = (row.get("image") or "").strip()
            if not image_value:
                msg = f"CSV row {row_number}: 'image' must not be empty"
                raise ValueError(msg)

            copies_value = (row.get("copies") or "1").strip()
            try:
                copies = int(copies_value)
            except ValueError as exc:
                msg = f"CSV row {row_number}: 'copies' must be an integer"
                raise ValueError(msg) from exc
            if copies < 1:
                msg = f"CSV row {row_number}: 'copies' must be at least 1"
                raise ValueError(msg)

            image_path = Path(image_value)
            if not image_path.is_absolute():
                image_path = base_dir / image_path
            if not image_path.is_file():
                msg = f"CSV row {row_number}: image not found: {image_path}"
                raise ValueError(msg)

            jobs.append(CsvPrintJob(path=image_path, copies=copies))

    if not jobs:
        msg = "CSV must contain at least one print job"
        raise ValueError(msg)

    return jobs
