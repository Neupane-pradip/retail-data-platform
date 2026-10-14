import os

import psycopg


INSERT_ORDER_SQL = """
    INSERT INTO public.orders AS existing (
        order_id,
        customer_id,
        order_date,
        total_amount,
        status
    )
    VALUES (%s, %s, %s, %s, %s)

    ON CONFLICT (order_id)
    DO UPDATE SET
        customer_id = EXCLUDED.customer_id,
        order_date = EXCLUDED.order_date,
        total_amount = EXCLUDED.total_amount,
        status = EXCLUDED.status

    WHERE (
        existing.customer_id,
        existing.order_date,
        existing.total_amount,
        existing.status
    ) IS DISTINCT FROM (
        EXCLUDED.customer_id,
        EXCLUDED.order_date,
        EXCLUDED.total_amount,
        EXCLUDED.status
    );
"""


def load_orders(orders: list[dict]) -> int:
    """Insert or update orders in one transaction; return changed row count."""
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
                    INSERT_ORDER_SQL,
                    (
                        order["order_id"],
                        order["customer_id"],
                        order["order_date"],
                        order["total_amount"],
                        order["status"],
                    ),
                )

                changed_count += cursor.rowcount

    return changed_count