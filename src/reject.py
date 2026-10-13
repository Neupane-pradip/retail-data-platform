import json
from pathlib import Path


def save_rejections(
    rejected_orders: list[dict],
    output_path: Path,
) -> None:
    """Save rejected records and their reasons as a JSON report."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        mode="w",
        encoding="utf-8",
    ) as file:
        json.dump(
            rejected_orders,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")