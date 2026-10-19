import csv
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg


MAX_INTEGER = 2147483647
MAX_PRICE = Decimal("9999999999.99")


def read_order_items(file_path: Path) -> list[dict[str, str]]:
    """Read order-item records from CSV."""
    with file_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def parse_positive_integer(value: str, field: str) -> int:
    """Parse a positive integer compatible with PostgreSQL INTEGER."""
    # Restrict the representation before conversion.
    if (
        not value.isascii()
        or not value.isdecimal()
        or len(value) > 10
    ):
        raise ValueError(
            f"{field} must be a positive integer"
        )

    number = int(value)

    if number < 1 or number > MAX_INTEGER:
        raise ValueError(
            f"{field} must be between 1 and {MAX_INTEGER}"
        )

    return number


def validate_order_item(row: dict[str, str]) -> dict:
    """Validate one line and convert numeric values."""
    required_fields = (
        "order_id",
        "line_number",
        "product_id",
        "quantity",
        "unit_price",
    )

    cleaned = {}

    for field in required_fields:
        value = row.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is missing or empty")

        cleaned[field] = value.strip()

    line_number = parse_positive_integer(
        cleaned["line_number"],
        "line_number",
    )

    quantity = parse_positive_integer(
        cleaned["quantity"],
        "quantity",
    )

    try:
        unit_price = Decimal(cleaned["unit_price"])
    except InvalidOperation:
        raise ValueError("unit_price must be a number") from None

    if not unit_price.is_finite():
        raise ValueError("unit_price must be finite")

    if unit_price < 0:
        raise ValueError("unit_price must not be negative")

    if unit_price > MAX_PRICE:
        raise ValueError("unit_price exceeds the supported maximum")

    if unit_price % Decimal("0.01") != 0:
        raise ValueError("unit_price must represent whole cents")

    return {
        "order_id": cleaned["order_id"],
        "line_number": line_number,
        "product_id": cleaned["product_id"],
        "quantity": quantity,
        "unit_price": unit_price,
    }


def load_order_items(items: list[dict]) -> int:
    """Insert new order lines in one transaction."""
    inserted_count = 0

    with psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=10,
    ) as connection:
        with connection.cursor() as cursor:
            for item in items:
                cursor.execute(
                    """
                    INSERT INTO public.order_items (
                        order_id,
                        line_number,
                        product_id,
                        quantity,
                        unit_price
                    )
                    VALUES (%s, %s, %s, %s, %s)

                    ON CONFLICT (order_id, line_number)
                    DO NOTHING;
                    """,
                    (
                        item["order_id"],
                        item["line_number"],
                        item["product_id"],
                        item["quantity"],
                        item["unit_price"],
                    ),
                )

                inserted_count += cursor.rowcount

    return inserted_count