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
from reject import save_rejections
from validate import validate_order


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CUSTOMERS_FILE = PROJECT_ROOT / "data" / "raw" / "customers.csv"
ORDERS_FILE = PROJECT_ROOT / "data" / "raw" / "orders.csv"

CUSTOMER_REJECTIONS_FILE = (
    PROJECT_ROOT / "data" / "rejected" / "customers_rejected.json"
)

ORDER_REJECTIONS_FILE = (
    PROJECT_ROOT / "data" / "rejected" / "orders_rejected.json"
)

LOG_FILE = PROJECT_ROOT / "logs" / "pipeline.log"

logger = logging.getLogger("retail_pipeline")


def run_customer_pipeline() -> None:
    """Read, validate, and load customers."""
    logger.info("Reading customers from %s", CUSTOMERS_FILE)

    rows = read_customers(CUSTOMERS_FILE)

    valid_customers = []
    rejected_customers = []

    for record_number, row in enumerate(rows, start=1):
        try:
            customer = validate_customer(row)

        except ValueError as error:
            rejected_customers.append(
                {
                    "record_number": record_number,
                    "raw_customer": row,
                    "reason": str(error),
                }
            )

            logger.warning(
                "Rejected customer record %s: %s",
                record_number,
                error,
            )

        else:
            valid_customers.append(customer)

    save_rejections(
        rejected_customers,
        CUSTOMER_REJECTIONS_FILE,
    )

    logger.info("Customers read: %s", len(rows))
    logger.info("Valid customers: %s", len(valid_customers))
    logger.info("Rejected customers: %s", len(rejected_customers))

    inserted_count = load_customers(valid_customers)
    skipped_count = len(valid_customers) - inserted_count

    logger.info("Customers inserted: %s", inserted_count)
    logger.info("Existing customer IDs skipped: %s", skipped_count)


def run_order_pipeline() -> None:
    """Read, validate, and load orders."""
    logger.info("Reading orders from %s", ORDERS_FILE)

    rows = read_orders(ORDERS_FILE)

    valid_orders = []
    rejected_orders = []

    for record_number, row in enumerate(rows, start=1):
        try:
            order = validate_order(row)

        except ValueError as error:
            rejected_orders.append(
                {
                    "record_number": record_number,
                    "raw_order": row,
                    "reason": str(error),
                }
            )

            logger.warning(
                "Rejected order record %s: %s",
                record_number,
                error,
            )

        else:
            valid_orders.append(order)

    save_rejections(
        rejected_orders,
        ORDER_REJECTIONS_FILE,
    )

    logger.info("Orders read: %s", len(rows))
    logger.info("Valid orders: %s", len(valid_orders))
    logger.info("Rejected orders: %s", len(rejected_orders))

    changed_count = load_orders(valid_orders)
    skipped_count = len(valid_orders) - changed_count

    logger.info("Orders inserted or updated: %s", changed_count)
    logger.info("Equal or older versions skipped: %s", skipped_count)


def run_pipeline() -> None:
    logger.info("Retail data pipeline started")

    run_customer_pipeline()
    run_order_pipeline()

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