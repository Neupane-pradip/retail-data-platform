import logging
from pathlib import Path

from dotenv import load_dotenv

from extract import read_orders
from load import load_orders
from logging_config import configure_logging
from reject import save_rejections
from validate import validate_order


PROJECT_ROOT = Path(__file__).resolve().parent.parent

ORDERS_FILE = PROJECT_ROOT / "data" / "raw" / "orders.csv"

REJECTIONS_FILE = (
    PROJECT_ROOT / "data" / "rejected" / "orders_rejected.json"
)

LOG_FILE = PROJECT_ROOT / "logs" / "pipeline.log"

logger = logging.getLogger("retail_pipeline")


def run_pipeline() -> None:
    """Read, validate, and load orders."""
    logger.info("Retail data pipeline started")
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
                "Rejected record %s: %s",
                record_number,
                error,
            )

        else:
            valid_orders.append(order)

    save_rejections(rejected_orders, REJECTIONS_FILE)

    logger.info("Orders read: %s", len(rows))
    logger.info("Valid orders: %s", len(valid_orders))
    logger.info("Rejected orders: %s", len(rejected_orders))
    logger.info("Rejection report saved to %s", REJECTIONS_FILE)

    changed_count = load_orders(valid_orders)
    unchanged_count = len(valid_orders) - changed_count

    logger.info("Orders inserted or updated: %s", changed_count)
    logger.info("Unchanged records skipped: %s", unchanged_count)
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