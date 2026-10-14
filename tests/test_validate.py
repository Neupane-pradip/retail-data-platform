import unittest
from datetime import date
from decimal import Decimal

from src.validate import validate_order


def make_valid_order() -> dict[str, str]:
    """Return a fresh valid input record for each test."""
    return {
        "order_id": "ORD001",
        "customer_id": "CUST001",
        "order_date": "2026-10-01",
        "total_amount": "49.90",
        "status": "completed",
    }


class TestValidateOrder(unittest.TestCase):

    def test_valid_order_returns_typed_values(self):
        row = make_valid_order()

        result = validate_order(row)

        self.assertEqual(result["order_id"], "ORD001")
        self.assertEqual(result["customer_id"], "CUST001")
        self.assertEqual(result["order_date"], date(2026, 10, 1))
        self.assertIsInstance(result["total_amount"], Decimal)
        self.assertEqual(result["total_amount"], Decimal("49.90"))
        self.assertEqual(result["status"], "completed")

    def test_empty_customer_id_is_rejected(self):
        row = make_valid_order()
        row["customer_id"] = "   "

        with self.assertRaisesRegex(
            ValueError,
            "customer_id is missing or empty",
        ):
            validate_order(row)

    def test_impossible_date_is_rejected(self):
        row = make_valid_order()
        row["order_date"] = "2026-02-30"

        with self.assertRaisesRegex(
            ValueError,
            "order_date must be a valid YYYY-MM-DD date",
        ):
            validate_order(row)

    def test_negative_amount_is_rejected(self):
        row = make_valid_order()
        row["total_amount"] = "-10.00"

        with self.assertRaisesRegex(
            ValueError,
            "total_amount must not be negative",
        ):
            validate_order(row)

    def test_fraction_of_a_cent_is_rejected(self):
        row = make_valid_order()
        row["total_amount"] = "10.001"

        with self.assertRaisesRegex(
            ValueError,
            "total_amount must represent whole cents",
        ):
            validate_order(row)

    def test_non_finite_amounts_are_rejected(self):
        for amount in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(amount=amount):
                row = make_valid_order()
                row["total_amount"] = amount

                with self.assertRaisesRegex(
                    ValueError,
                    "total_amount must be finite",
                ):
                    validate_order(row)

    def test_unknown_status_is_rejected(self):
        row = make_valid_order()
        row["status"] = "unknown"

        with self.assertRaisesRegex(
            ValueError,
            "status must be completed, cancelled, or refunded",
        ):
            validate_order(row)


if __name__ == "__main__":
    unittest.main()