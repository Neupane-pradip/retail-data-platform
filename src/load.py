import os

import psycopg


INSERT_ORDER_SQL = """
    INSERT INTO public.orders (
        order_id,
        customer_id,
        order_date,
        total_amount,
        status
    )
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (order_id) DO NOTHING;
"""


def load_orders(orders: list[dict]) -> int:
    """Insert new orders in one transaction and return the inserted count."""
    inserted_count = 0

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

                inserted_count += cursor.rowcount

    return inserted_count