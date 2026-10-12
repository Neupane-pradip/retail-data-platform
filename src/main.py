from pathlib import Path

from extract import read_orders


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORDERS_FILE = PROJECT_ROOT / "data" / "raw" / "orders.csv"


def main() -> None:
    print("Retail data pipeline started")

    orders = read_orders(ORDERS_FILE)

    print(f"Orders read: {len(orders)}")

    for order in orders:
        print(
            f"{order['order_id']} | "
            f"{order['customer_id']} | "
            f"{order['order_date']} | "
            f"EUR {order['total_amount']} | "
            f"{order['status']}"
        )


if __name__ == "__main__":
    main()