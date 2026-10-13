from datetime import date
from decimal import Decimal, InvalidOperation


ALLOWED_STATUSES = {"completed", "cancelled", "refunded"}


def validate_order(row: dict[str, str]) -> dict:
    """Validate one raw order and return its typed values."""
    required_fields = (
        "order_id",
        "customer_id",
        "order_date",
        "total_amount",
        "status",
    )

    cleaned = {}

    for field in required_fields:
        value = row.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is missing or empty")

        cleaned[field] = value.strip()

    # Parse the date and enforce the YYYY-MM-DD representation.
    try:
        order_date = date.fromisoformat(cleaned["order_date"])
    except ValueError:
        raise ValueError("order_date must be a valid YYYY-MM-DD date") from None

    if order_date.isoformat() != cleaned["order_date"]:
        raise ValueError("order_date must use YYYY-MM-DD format")

    # Parse money directly from the string to preserve decimal accuracy.
    try:
        amount = Decimal(cleaned["total_amount"])
    except InvalidOperation:
        raise ValueError("total_amount must be a number") from None

    if not amount.is_finite():
        raise ValueError("total_amount must be finite")

    if amount < 0:
        raise ValueError("total_amount must not be negative")

    # Check whole cents without rounding the input.
    if amount % Decimal("0.01") != 0:
        raise ValueError("total_amount must represent whole cents")

    status = cleaned["status"].lower()

    if status not in ALLOWED_STATUSES:
        raise ValueError(
            "status must be completed, cancelled, or refunded"
        )

    return {
        "order_id": cleaned["order_id"],
        "customer_id": cleaned["customer_id"],
        "order_date": order_date,
        "total_amount": amount,
        "status": status,
    }