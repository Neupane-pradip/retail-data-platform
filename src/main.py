import logging
from pathlib import Path

from dotenv import load_dotenv

from customers import (
    load_customers,
    read_customers,
    validate_customer,
)
from extract import read_orders
from load import load_orders
from logging_config import configure_logging
from order_items import (
    load_order_items,
    read_order_items,
    validate_order_item,
)
from products import (
    load_products,
    read_products,
    validate_product,
)
from reject import save_rejections
from validate import validate_order


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIRECTORY = PROJECT_ROOT / "data" / "raw"
REJECTED_DIRECTORY = PROJECT_ROOT / "data" / "rejected"
LOG_FILE = PROJECT_ROOT / "logs" / "pipeline.log"

logger = logging.getLogger("retail_pipeline")


def process_dataset(
    name,
    filename,
    reader,
    validator,
    loader,
    changed_label,
    skipped_label,
    raw_record_key,
):
    """Read, validate, report rejections, and load one dataset."""
    input_path = RAW_DIRECTORY / filename
    rejection_path = REJECTED_DIRECTORY / f"{name}_rejected.json"

    logger.info("Reading %s from %s", name, input_path)

    rows = reader(input_path)
    valid_records = []
    rejected_records = []

    for record_number, row in enumerate(rows, start=1):
        try:
            record = validator(row)

        except ValueError as error:
            rejected_records.append(
                {
                    "record_number": record_number,
                    raw_record_key: row,
                    "reason": str(error),
                }
            )

            logger.warning(
                "Rejected %s record %s: %s",
                name,
                record_number,
                error,
            )

        else:
            valid_records.append(record)

    save_rejections(rejected_records, rejection_path)

    logger.info("%s read: %s", name.capitalize(), len(rows))
    logger.info("Valid %s: %s", name, len(valid_records))
    logger.info("Rejected %s: %s", name, len(rejected_records))
    logger.info("Rejection report saved to %s", rejection_path)

    changed_count = loader(valid_records)
    skipped_count = len(valid_records) - changed_count

    logger.info("%s: %s", changed_label, changed_count)
    logger.info("%s: %s", skipped_label, skipped_count)


def run_pipeline() -> None:
    logger.info("Retail data pipeline started")

    process_dataset(
        name="customers",
        filename="customers.csv",
        reader=read_customers,
        validator=validate_customer,
        loader=load_customers,
        changed_label="Customers inserted",
        skipped_label="Existing customer IDs skipped",
        raw_record_key="raw_customer",
    )

    process_dataset(
        name="products",
        filename="products.csv",
        reader=read_products,
        validator=validate_product,
        loader=load_products,
        changed_label="Products inserted",
        skipped_label="Existing product IDs skipped",
        raw_record_key="raw_product",
    )

    process_dataset(
        name="orders",
        filename="orders.csv",
        reader=read_orders,
        validator=validate_order,
        loader=load_orders,
        changed_label="Orders inserted or updated",
        skipped_label="Equal or older versions skipped",
        raw_record_key="raw_order",
    )

    process_dataset(
        name="order_items",
        filename="order_items.csv",
        reader=read_order_items,
        validator=validate_order_item,
        loader=load_order_items,
        changed_label="Order items inserted",
        skipped_label="Existing order lines skipped",
        raw_record_key="raw_order_item",
    )

    logger.info("Retail data pipeline finished successfully")


def main() -> None:
    configure_logging(LOG_FILE)
    load_dotenv(PROJECT_ROOT / ".env")

    try:
        run_pipeline()

    except Exception:
        logger.exception("Retail data pipeline failed")
        raise


if __name__ == "__main__":
    main()