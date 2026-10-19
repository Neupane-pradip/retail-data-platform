import unittest
from decimal import Decimal

from src.order_items import validate_order_item


def make_valid_item():
    """Return a fresh synthetic order line."""
    return {
        "order_id": "ORD001",
        "line_number": "1",
        "product_id": "PROD004",
        "quantity": "2",
        "unit_price": "29.90",
    }


class TestValidateOrderItem(unittest.TestCase):

    def test_valid_item_returns_typed_values(self):
        result = validate_order_item(make_valid_item())

        self.assertEqual(
            result,
            {
                "order_id": "ORD001",
                "line_number": 1,
                "product_id": "PROD004",
                "quantity": 2,
                "unit_price": Decimal("29.90"),
            },
        )

        self.assertIsInstance(result["line_number"], int)
        self.assertIsInstance(result["quantity"], int)
        self.assertIsInstance(result["unit_price"], Decimal)

    def test_missing_fields_are_rejected(self):
        for field in make_valid_item():
            with self.subTest(field=field):
                row = make_valid_item()
                del row[field]

                with self.assertRaisesRegex(
                    ValueError,
                    f"{field} is missing or empty",
                ):
                    validate_order_item(row)

    def test_empty_and_non_string_fields_are_rejected(self):
        for field in make_valid_item():
            for value in ("", "   ", None, 123):
                with self.subTest(field=field, value=value):
                    row = make_valid_item()
                    row[field] = value

                    with self.assertRaisesRegex(
                        ValueError,
                        f"{field} is missing or empty",
                    ):
                        validate_order_item(row)

    def test_invalid_integer_values_are_rejected(self):
        examples = (
            "0",
            "-1",
            "1.5",
            "abc",
            "1e2",
            "2147483648",
        )

        for field in ("line_number", "quantity"):
            for value in examples:
                with self.subTest(field=field, value=value):
                    row = make_valid_item()
                    row[field] = value

                    with self.assertRaises(ValueError):
                        validate_order_item(row)

    def test_maximum_integer_is_accepted(self):
        row = make_valid_item()
        row["line_number"] = "2147483647"
        row["quantity"] = "2147483647"

        result = validate_order_item(row)

        self.assertEqual(result["line_number"], 2147483647)
        self.assertEqual(result["quantity"], 2147483647)

    def test_invalid_prices_are_rejected(self):
        examples = (
            ("abc", "unit_price must be a number"),
            ("NaN", "unit_price must be finite"),
            ("Infinity", "unit_price must be finite"),
            ("-Infinity", "unit_price must be finite"),
            ("-0.01", "unit_price must not be negative"),
            ("1.001", "unit_price must represent whole cents"),
            (
                "10000000000.00",
                "unit_price exceeds the supported maximum",
            ),
        )

        for value, message in examples:
            with self.subTest(price=value):
                row = make_valid_item()
                row["unit_price"] = value

                with self.assertRaisesRegex(ValueError, message):
                    validate_order_item(row)

    def test_zero_price_is_accepted(self):
        row = make_valid_item()
        row["unit_price"] = "0.00"

        result = validate_order_item(row)

        self.assertEqual(result["unit_price"], Decimal("0.00"))

    def test_equivalent_whole_cent_price_is_accepted(self):
        row = make_valid_item()
        row["unit_price"] = "29.900"

        result = validate_order_item(row)

        self.assertEqual(result["unit_price"], Decimal("29.90"))

    def test_cleaning_preserves_original_input(self):
        row = {
            "order_id": " ORD001 ",
            "line_number": " 1 ",
            "product_id": " PROD004 ",
            "quantity": " 2 ",
            "unit_price": " 29.90 ",
        }
        original = row.copy()

        result = validate_order_item(row)

        self.assertEqual(row, original)
        self.assertEqual(result["order_id"], "ORD001")
        self.assertEqual(result["product_id"], "PROD004")
        self.assertEqual(result["quantity"], 2)
        self.assertEqual(result["unit_price"], Decimal("29.90"))


if __name__ == "__main__":
    unittest.main()