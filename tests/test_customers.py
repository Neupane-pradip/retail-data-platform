import unittest

from src.customers import validate_customer


def make_valid_customer() -> dict[str, str]:
    """Return a fresh synthetic customer record."""
    return {
        "customer_id": "CUST001",
        "customer_name": "Aino Example",
        "city": "Tampere",
    }


class TestValidateCustomer(unittest.TestCase):

    def test_valid_customer_is_accepted(self):
        row = make_valid_customer()

        result = validate_customer(row)

        self.assertEqual(result, row)

    def test_surrounding_spaces_are_removed(self):
        row = {
            "customer_id": " CUST001 ",
            "customer_name": " Aino Example ",
            "city": " Tampere ",
        }

        result = validate_customer(row)

        self.assertEqual(
            result,
            {
                "customer_id": "CUST001",
                "customer_name": "Aino Example",
                "city": "Tampere",
            },
        )

    def test_missing_fields_are_rejected(self):
        for field in ("customer_id", "customer_name", "city"):
            with self.subTest(field=field):
                row = make_valid_customer()
                del row[field]

                with self.assertRaisesRegex(
                    ValueError,
                    f"{field} is missing or empty",
                ):
                    validate_customer(row)

    def test_blank_fields_are_rejected(self):
        for field in ("customer_id", "customer_name", "city"):
            for value in ("", "   "):
                with self.subTest(field=field, value=value):
                    row = make_valid_customer()
                    row[field] = value

                    with self.assertRaisesRegex(
                        ValueError,
                        f"{field} is missing or empty",
                    ):
                        validate_customer(row)

    def test_non_string_values_are_rejected(self):
        for field in ("customer_id", "customer_name", "city"):
            for value in (None, 123):
                with self.subTest(field=field, value=value):
                    row = make_valid_customer()
                    row[field] = value

                    with self.assertRaisesRegex(
                        ValueError,
                        f"{field} is missing or empty",
                    ):
                        validate_customer(row)

    def test_original_record_is_not_modified(self):
        row = {
            "customer_id": " CUST001 ",
            "customer_name": " Aino Example ",
            "city": " Tampere ",
        }
        original = row.copy()

        validate_customer(row)

        self.assertEqual(row, original)

    def test_names_and_cities_preserve_case_and_characters(self):
        row = {
            "customer_id": "CUST002",
            "customer_name": "Väinö Example",
            "city": "Jyväskylä",
        }

        result = validate_customer(row)

        self.assertEqual(result["customer_name"], "Väinö Example")
        self.assertEqual(result["city"], "Jyväskylä")


if __name__ == "__main__":
    unittest.main()