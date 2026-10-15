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
    """Open a connection using the project's database settings."""
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
        """A failed insert must roll back the whole batch."""
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
            # The second order violates the amount constraint.
            with self.assertRaises(
                psycopg.errors.CheckViolation
            ) as raised:
                load_orders(orders)

            self.assertEqual(
                raised.exception.diag.constraint_name,
                "orders_amount_valid",
            )

            # Neither order should remain after the failed batch.
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
            # Remove only this test's records if anything remains.
            with connect_to_database() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM public.orders
                        WHERE order_id IN (%s, %s);
                        """,
                        (first_id, second_id),
                    )

    def test_order_updates_and_replays(self):
        """Insert new orders, apply corrections, and skip replays."""
        load_dotenv(PROJECT_ROOT / ".env")

        order_id = f"TEST_{uuid4().hex}"

        order = {
            "order_id": order_id,
            "customer_id": "TEST_CUSTOMER",
            "order_date": date(2026, 10, 1),
            "total_amount": Decimal("49.90"),
            "status": "completed",
        }

        try:
            # First delivery: insert the new order.
            self.assertEqual(
                load_orders([order]),
                1,
                "A new order should be inserted",
            )

            # Identical delivery: skip the unchanged order.
            self.assertEqual(
                load_orders([order]),
                0,
                "An identical order should be skipped",
            )

            # Create a correction without changing the original input.
            corrected_order = {
                **order,
                "status": "refunded",
            }

            # Corrected delivery: update the stored order.
            self.assertEqual(
                load_orders([corrected_order]),
                1,
                "A corrected order should be updated",
            )

            # Repeated correction: skip the unchanged order.
            self.assertEqual(
                load_orders([corrected_order]),
                0,
                "An identical correction should be skipped",
            )

            # Verify the final stored values and row count.
            with connect_to_database() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT customer_id, total_amount, status
                        FROM public.orders
                        WHERE order_id = %s;
                        """,
                        (order_id,),
                    )

                    stored_rows = cursor.fetchall()

            self.assertEqual(
                stored_rows,
                [
                    (
                        "TEST_CUSTOMER",
                        Decimal("49.90"),
                        "refunded",
                    )
                ],
                "The database should contain one corrected order",
            )

        finally:
            # Remove only the order created by this test.
            with connect_to_database() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM public.orders
                        WHERE order_id = %s;
                        """,
                        (order_id,),
                    )


if __name__ == "__main__":
    unittest.main()