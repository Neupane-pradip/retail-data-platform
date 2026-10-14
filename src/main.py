from pathlib import Path

from dotenv import load_dotenv

from extract import read_orders
from load import load_orders
from reject import save_rejections
from validate import validate_order


PROJECT_ROOT = Path(__file__).resolve().parent.parent

ORDERS_FILE = PROJECT_ROOT / "data" / "raw" / "orders.csv"

REJECTIONS_FILE = (
    PROJECT_ROOT / "data" / "rejected" / "orders_rejected.json"
)


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    print("Retail data pipeline started")

    rows = read_orders(ORDERS_FILE)

    valid_orders = []
    rejected_orders = []

    for record_number, row in enumerate(rows, start=1):
        try:
            order = validate_order(row)

        except ValueError as error:
            rejected_orders.append(
                {
                    "record_number": record_number,
                    "raw_order": row,
                    "reason": str(error),
                }
            )

        else:
            valid_orders.append(order)

    save_rejections(rejected_orders, REJECTIONS_FILE)

    print(f"Orders read: {len(rows)}")
    print(f"Valid orders: {len(valid_orders)}")
    print(f"Rejected orders: {len(rejected_orders)}")

    inserted_count = load_orders(valid_orders)
    skipped_count = len(valid_orders) - inserted_count

    print(f"Orders inserted: {inserted_count}")
    print(f"Existing order IDs skipped: {skipped_count}")

    for rejection in rejected_orders:
        print(
            f"Rejected record {rejection['record_number']}: "
            f"{rejection['reason']}"
        )

    print("Retail data pipeline finished")


if __name__ == "__main__":
    main()