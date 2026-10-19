import os
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import psycopg
from dotenv import load_dotenv

from src.customers import load_customers
from src.load import load_orders


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def connect_to_database():
    """Connect using the configured test or local database."""
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

    @classmethod
    def setUpClass(cls):
        load_dotenv(PROJECT_ROOT / ".env")

    def setUp(self):
        """Create an independent customer for each test."""
        self.customer_id = f"TEST_CUSTOMER_{uuid4().hex}"
        self.order_ids = []

        self.customer = {
            "customer_id": self.customer_id,
            "customer_name": "Test Customer",
            "city": "Tampere",
        }

        # Registered before loading so cleanup also runs if setup fails.
        self.addCleanup(self.cleanup_records)

        self.assertEqual(load_customers([self.customer]), 1)

    def cleanup_records(self):
        """Remove child orders before removing their parent customer."""
        with connect_to_database() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM public.orders
                    WHERE order_id = ANY(%s);
                    """,
                    (self.order_ids,),
                )

                cursor.execute(
                    """
                    DELETE FROM public.customers
                    WHERE customer_id = %s;
                    """,
                    (self.customer_id,),
                )

    def make_order(
        self,
        status="completed",
        updated_hour=10,
    ):
        order_id = f"TEST_ORDER_{uuid4().hex}"
        self.order_ids.append(order_id)

        return {
            "order_id": order_id,
            "customer_id": self.customer_id,
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

    def fetch_order(self, order_id):
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

    def test_failed_batch_rolls_back_all_new_orders(self):
        first = self.make_order()
        invalid = self.make_order()
        invalid["total_amount"] = Decimal("-5.00")

        with self.assertRaises(
            psycopg.errors.CheckViolation
        ) as raised:
            load_orders([first, invalid])

        self.assertEqual(
            raised.exception.diag.constraint_name,
            "orders_amount_valid",
        )

        self.assertIsNone(self.fetch_order(first["order_id"]))
        self.assertIsNone(self.fetch_order(invalid["order_id"]))

    def test_order_updates_and_replays(self):
        original = self.make_order()

        correction = {
            **original,
            "status": "refunded",
            "source_updated_at": datetime(
                2026, 10, 15, 14, tzinfo=timezone.utc
            ),
        }

        self.assertEqual(load_orders([original]), 1)
        self.assertEqual(load_orders([original]), 0)

        self.assertEqual(load_orders([correction]), 1)
        self.assertEqual(load_orders([correction]), 0)

        self.assertEqual(
            self.fetch_order(original["order_id"]),
            (
                Decimal("49.90"),
                "refunded",
                correction["source_updated_at"],
            ),
        )

    def test_older_version_cannot_overwrite_newer_order(self):
        newest = self.make_order(
            status="refunded",
            updated_hour=14,
        )

        older = {
            **newest,
            "status": "completed",
            "source_updated_at": datetime(
                2026, 10, 15, 10, tzinfo=timezone.utc
            ),
        }

        self.assertEqual(load_orders([newest]), 1)
        self.assertEqual(load_orders([older]), 0)

        self.assertEqual(
            self.fetch_order(newest["order_id"]),
            (
                Decimal("49.90"),
                "refunded",
                newest["source_updated_at"],
            ),
        )

    def test_customer_replay_does_not_create_duplicates(self):
        # setUp already inserted this customer.
        self.assertEqual(load_customers([self.customer]), 0)

        with connect_to_database() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT customer_name, city
                    FROM public.customers
                    WHERE customer_id = %s;
                    """,
                    (self.customer_id,),
                )

                stored_rows = cursor.fetchall()

        self.assertEqual(
            stored_rows,
            [("Test Customer", "Tampere")],
        )

    def test_unknown_customer_rejects_and_rolls_back_batch(self):
        valid = self.make_order()
        invalid = self.make_order()

        invalid["customer_id"] = f"MISSING_{uuid4().hex}"

        with self.assertRaises(
            psycopg.errors.ForeignKeyViolation
        ) as raised:
            load_orders([valid, invalid])

        self.assertEqual(
            raised.exception.diag.constraint_name,
            "orders_customer_fk",
        )

        self.assertIsNone(self.fetch_order(valid["order_id"]))
        self.assertIsNone(self.fetch_order(invalid["order_id"]))


if __name__ == "__main__":
    unittest.main()