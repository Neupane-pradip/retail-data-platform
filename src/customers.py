import csv
import os
from pathlib import Path

import psycopg


def read_customers(file_path: Path) -> list[dict[str, str]]:
    """Read customer records from a CSV file."""
    with file_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def validate_customer(row: dict[str, str]) -> dict[str, str]:
    """Check required customer values and remove surrounding spaces."""
    required_fields = (
        "customer_id",
        "customer_name",
        "city",
    )

    cleaned = {}

    for field in required_fields:
        value = row.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is missing or empty")

        cleaned[field] = value.strip()

    return cleaned


def load_customers(customers: list[dict[str, str]]) -> int:
    """Insert new customers in one transaction."""
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
            for customer in customers:
                cursor.execute(
                    """
                    INSERT INTO public.customers (
                        customer_id,
                        customer_name,
                        city
                    )
                    VALUES (%s, %s, %s)
                    ON CONFLICT (customer_id) DO NOTHING;
                    """,
                    (
                        customer["customer_id"],
                        customer["customer_name"],
                        customer["city"],
                    ),
                )

                inserted_count += cursor.rowcount

    return inserted_count