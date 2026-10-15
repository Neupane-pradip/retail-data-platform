from datetime import date, datetime, timezone
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
        "source_updated_at",
    )

    cleaned = {}

    for field in required_fields:
        value = row.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is missing or empty")

        cleaned[field] = value.strip()

    try:
        order_date = date.fromisoformat(cleaned["order_date"])
    except ValueError:
        raise ValueError(
            "order_date must be a valid YYYY-MM-DD date"
        ) from None

    if order_date.isoformat() != cleaned["order_date"]:
        raise ValueError("order_date must use YYYY-MM-DD format")

    try:
        amount = Decimal(cleaned["total_amount"])
    except InvalidOperation:
        raise ValueError("total_amount must be a number") from None

    if not amount.is_finite():
        raise ValueError("total_amount must be finite")

    if amount < 0:
        raise ValueError("total_amount must not be negative")

    # Match the maximum value supported by NUMERIC(12, 2).
    if amount > Decimal("9999999999.99"):
        raise ValueError("total_amount exceeds the supported maximum")

    if amount % Decimal("0.01") != 0:
        raise ValueError("total_amount must represent whole cents")

    status = cleaned["status"].lower()

    if status not in ALLOWED_STATUSES:
        raise ValueError(
            "status must be completed, cancelled, or refunded"
        )

    timestamp_text = cleaned["source_updated_at"]

    if "T" not in timestamp_text:
        raise ValueError(
            "source_updated_at must contain a date and time separated by T"
        )

    try:
        source_updated_at = datetime.fromisoformat(timestamp_text)
    except ValueError:
        raise ValueError(
            "source_updated_at must be a valid ISO timestamp"
        ) from None

    if (
        source_updated_at.tzinfo is None
        or source_updated_at.utcoffset() is None
    ):
        raise ValueError(
            "source_updated_at must include a timezone offset"
        )

    source_updated_at = source_updated_at.astimezone(timezone.utc)

    return {
        "order_id": cleaned["order_id"],
        "customer_id": cleaned["customer_id"],
        "order_date": order_date,
        "total_amount": amount,
        "status": status,
        "source_updated_at": source_updated_at,
    }