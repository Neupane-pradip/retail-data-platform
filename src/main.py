from pathlib import Path

from extract import read_orders
from validate import validate_order


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORDERS_FILE = PROJECT_ROOT / "data" / "raw" / "orders.csv"


def main() -> None:
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

    print(f"Orders read: {len(rows)}")
    print(f"Valid orders: {len(valid_orders)}")
    print(f"Rejected orders: {len(rejected_orders)}")

    for order in valid_orders:
        print(
            f"{order['order_id']} | "
            f"{order['order_date']} | "
            f"EUR {order['total_amount']:.2f} | "
            f"{order['status']}"
        )

    for rejection in rejected_orders:
        print(
            f"Rejected record {rejection['record_number']}: "
            f"{rejection['reason']}"
        )


if __name__ == "__main__":
    main()