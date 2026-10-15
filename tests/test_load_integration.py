import os
import unittest
from datetime import date, datetime, timezone
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


def make_order(
    order_id: str,
    status: str = "completed",
    updated_hour: int = 10,
) -> dict:
    """Create a typed synthetic order."""
    return {
        "order_id": order_id,
        "customer_id": "TEST_CUSTOMER",
        "order_date": date(2026, 10, 1),
        "total_amount": Decimal("49.90"),
        "status": status,
        "source_updated_at": datetime(
            2026,
            10,
            15,
            updated_hour,
            tzinfo=timezone.utc,
        ),
    }


def delete_test_orders(order_ids: list[str]) -> None:
    """Delete only the generated test orders."""
    with connect_to_database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM public.orders
                WHERE order_id = ANY(%s);
                """,
                (order_ids,),
            )


def fetch_order(order_id: str):
    """Read the fields checked by the integration tests."""
    with connect_to_database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT total_amount, status, source_updated_at
                FROM public.orders
                WHERE order_id = %s;
                """,
                (order_id,),
            )

            return cursor.fetchone()


@unittest.skipUnless(
    os.environ.get("RUN_DB_TESTS") == "1",
    "Set RUN_DB_TESTS=1 to run database integration tests",
)
class TestLoadOrdersIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        load_dotenv(PROJECT_ROOT / ".env")

    def test_failed_batch_rolls_back_all_new_orders(self):
        batch_id = uuid4().hex
        first_id = f"TEST_{batch_id}_1"
        second_id = f"TEST_{batch_id}_2"

        first_order = make_order(first_id)
        invalid_order = make_order(second_id)
        invalid_order["total_amount"] = Decimal("-5.00")

        try:
            with self.assertRaises(
                psycopg.errors.CheckViolation
            ) as raised:
                load_orders([first_order, invalid_order])

            self.assertEqual(
                raised.exception.diag.constraint_name,
                "orders_amount_valid",
            )

            self.assertIsNone(fetch_order(first_id))
            self.assertIsNone(fetch_order(second_id))

        finally:
            delete_test_orders([first_id, second_id])

    def test_order_updates_and_replays(self):
        order_id = f"TEST_{uuid4().hex}"

        original = make_order(order_id, updated_hour=10)

        correction = make_order(
            order_id,
            status="refunded",
            updated_hour=14,
        )

        try:
            self.assertEqual(load_orders([original]), 1)
            self.assertEqual(load_orders([original]), 0)

            self.assertEqual(load_orders([correction]), 1)
            self.assertEqual(load_orders([correction]), 0)

            self.assertEqual(
                fetch_order(order_id),
                (
                    Decimal("49.90"),
                    "refunded",
                    correction["source_updated_at"],
                ),
            )

        finally:
            delete_test_orders([order_id])

    def test_older_version_cannot_overwrite_newer_order(self):
        order_id = f"TEST_{uuid4().hex}"

        newest = make_order(
            order_id,
            status="refunded",
            updated_hour=14,
        )

        older = make_order(
            order_id,
            status="completed",
            updated_hour=10,
        )

        try:
            self.assertEqual(load_orders([newest]), 1)
            self.assertEqual(load_orders([older]), 0)

            self.assertEqual(
                fetch_order(order_id),
                (
                    Decimal("49.90"),
                    "refunded",
                    newest["source_updated_at"],
                ),
            )

        finally:
            delete_test_orders([order_id])


if __name__ == "__main__":
    unittest.main()