import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent


RECONCILIATION_SQL = """
    WITH item_totals AS (
        SELECT
            order_id,
            COUNT(*) AS line_count,
            SUM(quantity * unit_price) AS items_total
        FROM public.order_items
        GROUP BY order_id
    )
    SELECT
        o.order_id,
        o.total_amount,
        COALESCE(t.items_total, 0) AS items_total,
        CASE
            WHEN t.order_id IS NULL THEN 'MISSING ITEMS'
            ELSE 'TOTAL MISMATCH'
        END AS reason
    FROM public.orders AS o
    LEFT JOIN item_totals AS t
        ON o.order_id = t.order_id
    WHERE
        t.order_id IS NULL
        OR o.total_amount <> t.items_total
    ORDER BY o.order_id;
"""


def check_reconciliation() -> None:
    """Raise an error if any stored order fails reconciliation."""
    with psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=10,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(RECONCILIATION_SQL)
            failures = cursor.fetchall()

            cursor.execute("SELECT COUNT(*) FROM public.orders;")
            order_count = cursor.fetchone()[0]

    if order_count == 0:
        raise ValueError(
            "Reconciliation failed: there are no stored orders to check"
        )

    if failures:
        for order_id, order_total, items_total, reason in failures:
            print(
                f"FAIL | {order_id} | {reason} | "
                f"order_total={order_total} | "
                f"items_total={items_total}"
            )

        raise ValueError(
            f"Reconciliation failed for {len(failures)} order(s)"
        )

    print(f"PASS | All {order_count} orders reconcile with their items")


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    check_reconciliation()


if __name__ == "__main__":
    main()