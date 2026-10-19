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
from src.order_items import load_order_items
from src.products import load_products


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def connect_to_database():
    """Connect using local or CI environment settings."""
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
class TestOrderItemsIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        load_dotenv(PROJECT_ROOT / ".env")

    def setUp(self):
        """Create independent parent records for each test."""
        unique_id = uuid4().hex

        self.customer_id = f"TEST_CUSTOMER_{unique_id}"
        self.product_id = f"TEST_PRODUCT_{unique_id}"
        self.order_id = f"TEST_ORDER_{unique_id}"

        self.addCleanup(self.cleanup_records)

        self.assertEqual(
            load_customers(
                [
                    {
                        "customer_id": self.customer_id,
                        "customer_name": "Test Customer",
                        "city": "Tampere",
                    }
                ]
            ),
            1,
        )

        self.product = {
            "product_id": self.product_id,
            "product_name": "Test Product",
            "category": "Test Category",
            "current_price": Decimal("9.90"),
        }

        self.assertEqual(load_products([self.product]), 1)

        self.assertEqual(
            load_orders(
                [
                    {
                        "order_id": self.order_id,
                        "customer_id": self.customer_id,
                        "order_date": date(2026, 10, 1),
                        "total_amount": Decimal("15.00"),
                        "status": "completed",
                        "source_updated_at": datetime(
                            2026,
                            10,
                            15,
                            10,
                            tzinfo=timezone.utc,
                        ),
                    }
                ]
            ),
            1,
        )

    def cleanup_records(self):
        """Delete test data in child-to-parent order."""
        with connect_to_database() as connection:
            with connection.cursor() as cursor:
                # Cover lines referencing either generated parent.
                cursor.execute(
                    """
                    DELETE FROM public.order_items
                    WHERE order_id = %s OR product_id = %s;
                    """,
                    (self.order_id, self.product_id),
                )

                cursor.execute(
                    """
                    DELETE FROM public.orders
                    WHERE order_id = %s;
                    """,
                    (self.order_id,),
                )

                cursor.execute(
                    """
                    DELETE FROM public.products
                    WHERE product_id = %s;
                    """,
                    (self.product_id,),
                )

                cursor.execute(
                    """
                    DELETE FROM public.customers
                    WHERE customer_id = %s;
                    """,
                    (self.customer_id,),
                )

    def make_item(self, line_number=1):
        return {
            "order_id": self.order_id,
            "line_number": line_number,
            "product_id": self.product_id,
            "quantity": 2,
            "unit_price": Decimal("7.50"),
        }

    def fetch_items(self):
        with connect_to_database() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        line_number,
                        product_id,
                        quantity,
                        unit_price
                    FROM public.order_items
                    WHERE order_id = %s
                    ORDER BY line_number;
                    """,
                    (self.order_id,),
                )

                return cursor.fetchall()

    def test_valid_item_is_stored_with_historical_price(self):
        item = self.make_item()

        self.assertEqual(load_order_items([item]), 1)

        self.assertEqual(
            self.fetch_items(),
            [
                (
                    1,
                    self.product_id,
                    2,
                    Decimal("7.50"),
                )
            ],
        )

    def test_repeated_item_is_skipped(self):
        item = self.make_item()

        self.assertEqual(load_order_items([item]), 1)
        self.assertEqual(load_order_items([item]), 0)
        self.assertEqual(len(self.fetch_items()), 1)

    def test_product_replay_is_skipped(self):
        self.assertEqual(load_products([self.product]), 0)

        with connect_to_database() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT product_name, category, current_price
                    FROM public.products
                    WHERE product_id = %s;
                    """,
                    (self.product_id,),
                )

                rows = cursor.fetchall()

        self.assertEqual(
            rows,
            [
                (
                    "Test Product",
                    "Test Category",
                    Decimal("9.90"),
                )
            ],
        )

    def test_unknown_product_rolls_back_batch(self):
        valid = self.make_item(line_number=1)
        invalid = self.make_item(line_number=2)
        invalid["product_id"] = f"MISSING_{uuid4().hex}"

        with self.assertRaises(
            psycopg.errors.ForeignKeyViolation
        ) as raised:
            load_order_items([valid, invalid])

        self.assertEqual(
            raised.exception.diag.constraint_name,
            "order_items_product_fk",
        )

        self.assertEqual(self.fetch_items(), [])

    def test_unknown_order_rolls_back_batch(self):
        valid = self.make_item(line_number=1)
        invalid = self.make_item(line_number=2)
        invalid["order_id"] = f"MISSING_{uuid4().hex}"

        with self.assertRaises(
            psycopg.errors.ForeignKeyViolation
        ) as raised:
            load_order_items([valid, invalid])

        self.assertEqual(
            raised.exception.diag.constraint_name,
            "order_items_order_fk",
        )

        self.assertEqual(self.fetch_items(), [])

    def test_invalid_quantity_rolls_back_batch(self):
        valid = self.make_item(line_number=1)
        invalid = self.make_item(line_number=2)
        invalid["quantity"] = 0

        with self.assertRaises(
            psycopg.errors.CheckViolation
        ) as raised:
            load_order_items([valid, invalid])

        self.assertEqual(
            raised.exception.diag.constraint_name,
            "order_items_quantity_positive",
        )

        self.assertEqual(self.fetch_items(), [])


if __name__ == "__main__":
    unittest.main()