# Retail Data Platform

A data engineering learning project that processes retail orders from
CSV files and stores validated records in PostgreSQL.

The project focuses on reliable loading, handling corrections, testing
failures, and checking reporting totals.

## Pipeline

CSV → Validation → PostgreSQL → SQL reports

Invalid records are saved separately with rejection reasons.
Pipeline activity and failures are recorded in a log file.

## Tools used

- Python
- PostgreSQL
- Docker Compose
- Psycopg
- python-dotenv
- unittest
- Git and GitHub

## What I have built

### CSV extraction and validation

The pipeline reads synthetic retail orders and checks:

- Required fields are present and non-empty.
- Order dates are valid.
- Amounts are finite, non-negative, and representable in whole cents.
- Amounts fit the database column.
- Statuses are completed, cancelled, or refunded.
- Source update timestamps include timezone information.

Money is converted to Python `Decimal`, and source timestamps are
normalised to UTC.

### Rejection reporting

Invalid records are saved to a JSON report with their original values,
record numbers, and rejection reasons.

The report is replaced on each run.

### PostgreSQL storage

The orders table uses a primary key and constraints to protect stored data.

Valid orders are loaded in one transaction. If a database operation fails,
the transaction is rolled back to prevent partial writes.

### Order corrections and repeated deliveries

The loader uses source timestamps to decide whether to update an order.

| Incoming record | Action |
|---|---|
| New order ID | Insert |
| Existing order without a source timestamp | Accept timestamped record |
| Newer source version | Update |
| Equal or older source version | Skip |

Repeating the same input does not create duplicate orders or change
already matching versions.

### Logging

Timestamped logs record progress, rejection warnings, loading counts,
and failures.

Messages appear in the terminal and are appended to a log file.

### Automated testing

The current suite contains 10 passing tests covering:

- Valid data conversion.
- Invalid fields, dates, amounts, and statuses.
- Transaction rollback after a failed insert.
- Order corrections and repeated deliveries.
- Protection against older updates overwriting newer records.

Database tests use uniquely named synthetic orders and clean them up afterward.

### SQL reporting and reconciliation

Saved SQL queries report:

- Order counts and values by current status.
- Daily summaries by original order date.
- Total orders and distinct customers.
- Missing source update timestamps.

The results were manually checked against the valid sample records.

## Verified sample results

The sample contains eight records: five valid and three rejected.

| Metric | Result |
|---|---:|
| Stored orders | 5 |
| Distinct customers | 3 |
| Completed-order value | €199.99 |
| Refunded-order value | €74.90 |
| Cancelled-order value | €35.50 |
| Total value across all statuses | €310.39 |
| Missing source timestamps after loading | 0 |

These amounts describe orders by their current status, not accounting
revenue or payment-event history.

## Main project files

| Location | Purpose |
|---|---|
| `src/` | Extraction, validation, loading, and logging code |
| `data/raw/orders.csv` | Synthetic source records |
| `sql/001_create_orders.sql` | Initial orders table |
| `sql/002_add_source_updated_at.sql` | Source timestamp migration |
| `sql/003_order_reports.sql` | Reports and control totals |
| `tests/` | Validation and database integration tests |

## Current limitations

- Equal timestamps with conflicting values are skipped without an alert.
- Files are read into memory.
- Rejection reports and database changes are separate operations.
- Reconciliation is currently manual.
- Order status history and individual payment events are not stored.
- This project is a local learning implementation.

## What I am learning

Python data processing, SQL, database constraints, transactions, upserts,
source version handling, logging, testing, and data reconciliation.

## Next steps

- Automate tests with GitHub Actions.
- Add more timestamp-validation tests.
- Detect conflicting source records.
- Automate reconciliation.
- Extend the model with customers, products, and order items.