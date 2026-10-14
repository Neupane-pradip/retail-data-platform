import os
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import psycopg
from dotenv import load_dotenv

from src.load import load_orders


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def connect_to_database():
    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=10,
    )


@unittest.skipUnless(
    os.environ.get("RUN_DB_TESTS") == "1",
    "Set RUN_DB_TESTS=1 to run database integration tests",
)
class TestLoadOrdersIntegration(unittest.TestCase):

    def test_failed_batch_rolls_back_all_new_orders(self):
        load_dotenv(PROJECT_ROOT / ".env")

        batch_id = uuid4().hex
        first_id = f"TEST_{batch_id}_1"
        second_id = f"TEST_{batch_id}_2"

        orders = [
            {
                "order_id": first_id,
                "customer_id": "TEST_CUSTOMER",
                "order_date": date(2026, 10, 1),
                "total_amount": Decimal("10.00"),
                "status": "completed",
            },
            {
                "order_id": second_id,
                "customer_id": "TEST_CUSTOMER",
                "order_date": date(2026, 10, 1),
                "total_amount": Decimal("-5.00"),
                "status": "completed",
            },
        ]

        try:
            with self.assertRaises(
                psycopg.errors.CheckViolation
            ) as raised:
                load_orders(orders)

            self.assertEqual(
                raised.exception.diag.constraint_name,
                "orders_amount_valid",
            )

            with connect_to_database() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT COUNT(*)
                        FROM public.orders
                        WHERE order_id IN (%s, %s);
                        """,
                        (first_id, second_id),
                    )

                    stored_count = cursor.fetchone()[0]

            self.assertEqual(
                stored_count,
                0,
                "A failed batch left partially written orders",
            )

        finally:
            with connect_to_database() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM public.orders
                        WHERE order_id IN (%s, %s);
                        """,
                        (first_id, second_id),
                    )


if __name__ == "__main__":
    unittest.main()