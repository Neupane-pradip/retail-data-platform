import csv
from pathlib import Path

def read_orders(file_path: Path) -> list[dict[str, str]]:
    """Read an orders CSV and return its records as dictionaries."""
    with file_path.open(
        mode = "r",
        encoding = "utf-8",
        newline = "",
    )as file:
        reader = csv.DictReader(file)
        return list(reader)