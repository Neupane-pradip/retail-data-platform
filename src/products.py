import csv
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg


def read_products(file_path: Path) -> list[dict[str, str]]:
    """Read product records from CSV."""
    with file_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def validate_product(row: dict[str, str]) -> dict:
    """Validate a product and convert its price to Decimal."""
    required_fields = (
        "product_id",
        "product_name",
        "category",
        "current_price",
    )

    cleaned = {}

    for field in required_fields:
        value = row.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is missing or empty")

        cleaned[field] = value.strip()

    try:
        price = Decimal(cleaned["current_price"])
    except InvalidOperation:
        raise ValueError("current_price must be a number") from None

    if not price.is_finite():
        raise ValueError("current_price must be finite")

    if price < 0:
        raise ValueError("current_price must not be negative")

    if price > Decimal("9999999999.99"):
        raise ValueError("current_price exceeds the supported maximum")

    if price % Decimal("0.01") != 0:
        raise ValueError("current_price must represent whole cents")

    return {
        "product_id": cleaned["product_id"],
        "product_name": cleaned["product_name"],
        "category": cleaned["category"],
        "current_price": price,
    }


def load_products(products: list[dict]) -> int:
    """Insert new products in one transaction."""
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
            for product in products:
                cursor.execute(
                    """
                    INSERT INTO public.products (
                        product_id,
                        product_name,
                        category,
                        current_price
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (product_id) DO NOTHING;
                    """,
                    (
                        product["product_id"],
                        product["product_name"],
                        product["category"],
                        product["current_price"],
                    ),
                )

                inserted_count += cursor.rowcount

    return inserted_count