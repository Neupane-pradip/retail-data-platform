import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from io import StringIO
from unittest.mock import MagicMock, patch

from src.reconcile import check_reconciliation


class TestReconciliation(unittest.TestCase):

    def run_with_results(self, failures, order_count):
        connection = MagicMock()
        cursor = (
            connection.__enter__.return_value
            .cursor.return_value.__enter__.return_value
        )

        cursor.fetchall.return_value = failures
        cursor.fetchone.return_value = (order_count,)

        with patch(
            "src.reconcile.psycopg.connect",
            return_value=connection,
        ):
            with patch.dict(
                "os.environ",
                {
                    "POSTGRES_HOST": "127.0.0.1",
                    "POSTGRES_PORT": "5432",
                    "POSTGRES_DB": "test_db",
                    "POSTGRES_USER": "test_user",
                    "POSTGRES_PASSWORD": "test_password",
                },
            ):
                check_reconciliation()

    def test_matching_orders_pass(self):
        output = StringIO()

        with redirect_stdout(output):
            self.run_with_results([], 5)

        self.assertIn(
            "PASS | All 5 orders reconcile",
            output.getvalue(),
        )

    def test_empty_database_fails(self):
        with self.assertRaisesRegex(
            ValueError,
            "no stored orders",
        ):
            self.run_with_results([], 0)

    def test_missing_items_fail(self):
        failures = [
            (
                "TEST001",
                Decimal("10.00"),
                Decimal("0.00"),
                "MISSING ITEMS",
            )
        ]

        with redirect_stdout(StringIO()):
            with self.assertRaisesRegex(
                ValueError,
                "failed for 1 order",
            ):
                self.run_with_results(failures, 1)

    def test_mismatched_totals_fail(self):
        failures = [
            (
                "TEST002",
                Decimal("10.00"),
                Decimal("9.00"),
                "TOTAL MISMATCH",
            )
        ]

        with redirect_stdout(StringIO()):
            with self.assertRaisesRegex(
                ValueError,
                "failed for 1 order",
            ):
                self.run_with_results(failures, 1)


if __name__ == "__main__":
    unittest.main()
