import unittest
from decimal import Decimal

from src.products import validate_product


def make_valid_product():
    return {
        "product_id": "PROD001",
        "product_name": "Filter Coffee",
        "category": "Groceries",
        "current_price": "6.90",
    }


class TestValidateProduct(unittest.TestCase):

    def test_valid_product_returns_decimal_price(self):
        result = validate_product(make_valid_product())

        self.assertEqual(result["product_id"], "PROD001")
        self.assertIsInstance(result["current_price"], Decimal)
        self.assertEqual(result["current_price"], Decimal("6.90"))

    def test_required_fields_are_checked(self):
        for field in make_valid_product():
            for invalid_value in (None, "", "   ", 123):
                with self.subTest(field=field, value=invalid_value):
                    row = make_valid_product()
                    row[field] = invalid_value

                    with self.assertRaisesRegex(
                        ValueError,
                        f"{field} is missing or empty",
                    ):
                        validate_product(row)

    def test_invalid_prices_are_rejected(self):
        examples = (
            ("abc", "current_price must be a number"),
            ("NaN", "current_price must be finite"),
            ("Infinity", "current_price must be finite"),
            ("-1.00", "current_price must not be negative"),
            ("6.901", "current_price must represent whole cents"),
            (
                "10000000000.00",
                "current_price exceeds the supported maximum",
            ),
        )

        for value, message in examples:
            with self.subTest(price=value):
                row = make_valid_product()
                row["current_price"] = value

                with self.assertRaisesRegex(ValueError, message):
                    validate_product(row)

    def test_zero_price_is_allowed(self):
        row = make_valid_product()
        row["current_price"] = "0.00"

        result = validate_product(row)

        self.assertEqual(result["current_price"], Decimal("0.00"))

    def test_cleaning_preserves_original_input(self):
        row = {
            "product_id": " PROD001 ",
            "product_name": " Filter Coffee ",
            "category": " Groceries ",
            "current_price": " 6.90 ",
        }
        original = row.copy()

        result = validate_product(row)

        self.assertEqual(row, original)
        self.assertEqual(result["product_name"], "Filter Coffee")
        self.assertEqual(result["category"], "Groceries")
        self.assertEqual(result["current_price"], Decimal("6.90"))


if __name__ == "__main__":
    unittest.main()