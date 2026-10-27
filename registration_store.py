"""Private, local CSV storage for hackathon registrations."""

import csv
import os
import tempfile
import threading
from pathlib import Path


REGISTRATION_HEADERS = (
    "timestamp",
    "name",
    "email",
    "university",
    "degree",
    "team_name",
    "team_size",
    "experience",
    "interest",
    "open_for_joining",
    "open_spots",
    "student_id",
)

_CSV_LOCK = threading.RLock()


class CSVRegistrationStore:
    """CSV-backed subset of the worksheet operations used by the Team Hub."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def get_all_values(self) -> list[list[str]]:
        with _CSV_LOCK:
            if not self.path.exists():
                return [list(REGISTRATION_HEADERS)]

            with self.path.open("r", newline="", encoding="utf-8-sig") as file:
                rows = list(csv.reader(file))
            if not rows:
                return [list(REGISTRATION_HEADERS)]

            header = rows[0]
            original_header = header.copy()
            for name in REGISTRATION_HEADERS:
                if name not in header:
                    header.append(name)
            normalized = [header]
            normalized.extend(
                row + [""] * (len(header) - len(row))
                for row in rows[1:]
            )
            if header != original_header or any(
                len(row) != len(header) for row in rows[1:]
            ):
                self._write_rows(normalized)
            return normalized

    def append_row(self, values: list[str]) -> None:
        with _CSV_LOCK:
            rows = self.get_all_values()
            if len(values) > len(rows[0]):
                raise ValueError("Registration row has more fields than the CSV header.")
            rows.append([str(value) for value in values] + [""] * (len(rows[0]) - len(values)))
            self._write_rows(rows)

    def update_cell(self, row_number: int, column_number: int, value: str) -> None:
        with _CSV_LOCK:
            rows = self.get_all_values()
            if row_number < 1 or row_number > len(rows):
                raise IndexError(f"CSV row {row_number} does not exist.")
            if column_number < 1 or column_number > len(rows[0]):
                raise IndexError(f"CSV column {column_number} does not exist.")
            rows[row_number - 1][column_number - 1] = str(value)
            self._write_rows(rows)

    def _write_rows(self, rows: list[list[str]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                newline="",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as file:
                temp_path = Path(file.name)
                csv.writer(file).writerows(rows)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_path, self.path)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()
