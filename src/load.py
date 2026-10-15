import os

import psycopg


UPSERT_ORDER_SQL = """
    INSERT INTO public.orders AS existing (
        order_id,
        customer_id,
        order_date,
        total_amount,
        status,
        source_updated_at
    )
    VALUES (%s, %s, %s, %s, %s, %s)

    ON CONFLICT (order_id)
    DO UPDATE SET
        customer_id = EXCLUDED.customer_id,
        order_date = EXCLUDED.order_date,
        total_amount = EXCLUDED.total_amount,
        status = EXCLUDED.status,
        source_updated_at = EXCLUDED.source_updated_at

    WHERE
        existing.source_updated_at IS NULL
        OR EXCLUDED.source_updated_at > existing.source_updated_at;
"""


def load_orders(orders: list[dict]) -> int:
    """Insert new orders or apply newer versions in one transaction."""
    changed_count = 0

    with psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=10,
    ) as connection:
        with connection.cursor() as cursor:
            for order in orders:
                cursor.execute(
                    UPSERT_ORDER_SQL,
                    (
                        order["order_id"],
                        order["customer_id"],
                        order["order_date"],
                        order["total_amount"],
                        order["status"],
                        order["source_updated_at"],
                    ),
                )

                changed_count += cursor.rowcount

    return changed_count