# Retail Data Platform

A data engineering learning project that processes synthetic retail data
and stores validated records in PostgreSQL.

The ingestion stage covers customers, products, orders, and order items.
It focuses on reliable loading, data relationships, testing, and reporting.

## Pipeline

Customers → Products → Orders → Order items → Reconciliation

Each dataset is read from CSV, validated, and loaded into PostgreSQL.
Invalid input records are saved separately with rejection reasons.

## Tools used

Python, PostgreSQL, Docker Compose, Psycopg, python-dotenv,
unittest, Git, GitHub, and GitHub Actions.

## Data model

| Table | One row represents |
|---|---|
| `customers` | One customer |
| `products` | One product |
| `orders` | One order |
| `order_items` | One line within an order |

Orders reference existing customers. Order items reference existing orders
and products. An item is identified by its order ID and line number.

Order-item prices preserve the selling price, independently of the
product's current catalogue price.

## Implemented features

### Extraction and validation

The pipeline reads CSV files and checks required fields, dates,
statuses, integer quantities, and monetary values.

Money is converted directly from text to Python `Decimal`.
Order source timestamps must include timezone information and are
normalised to UTC.

### Rejection reports and logging

Invalid records are saved as JSON with their original values and reasons.
Each dataset's rejection report is replaced on every run.

Timestamped logs record progress, warnings, loading counts, and failures.
Logs appear in the terminal and are appended to a file.

### Reliable database loading

Each dataset is loaded in its own transaction. A database failure rolls
back that dataset's load.

Primary keys prevent duplicate identities. Foreign keys enforce valid
customer, order, and product references.

| Dataset | Existing-record policy |
|---|---|
| Customers | Skip existing customer IDs |
| Products | Skip existing product IDs |
| Orders | Apply only newer source versions |
| Order items | Skip existing order ID and line-number pairs |

Replaying the supplied files does not create duplicate records.

### Order version handling

New orders are inserted. Existing orders are updated only when the source
timestamp is newer, or the stored source timestamp is unknown.

Equal or older versions are skipped. This prevents an older delivery
from overwriting newer order information.

### Reporting and reconciliation

SQL reports summarise order counts and values by status and order date.

The reconciliation command checks that every stored order has items
and that its item total equals its order total. Missing items, mismatches,
or an empty orders table cause the check to fail.

The sample assumes no separate shipping charges, additional taxes,
or order-level discounts.

## Sample dataset

| Dataset | Records |
|---|---:|
| Customers | 3 |
| Products | 5 |
| Source orders | 8 |
| Valid stored orders | 5 |
| Rejected orders | 3 |
| Order items | 10 |

The rejected orders contain a negative amount, an invalid date,
and an unsupported status.

## Verified business totals

| Metric | Value |
|---|---:|
| Completed-order value | €199.99 |
| Refunded-order value | €74.90 |
| Cancelled-order value | €35.50 |
| Total order value across statuses | €310.39 |

All five sample order totals match their item totals.

These figures describe current order status, not accounting revenue.
Refunds are grouped by original order date, not refund-event date.

## Automated checks

Tests cover validation, repeated deliveries, order corrections,
stale-version protection, foreign keys, transaction rollback,
historical selling prices, and reconciliation outcomes.

GitHub Actions creates a temporary PostgreSQL database, applies schema
migrations, runs the tests, loads the sample data, and checks reconciliation
before and after replaying the input.

## Main project files

| Location | Purpose |
|---|---|
| `src/` | Pipeline, validation, loading, logging, and reconciliation |
| `data/raw/` | Synthetic source CSV files |
| `sql/` | Schema changes and reporting queries |
| `tests/` | Unit and database integration tests |
| `.github/workflows/tests.yml` | Automated checks on GitHub |

## Current limitations

- Customer, product, and item corrections are not applied.
- Equal order timestamps with conflicting values are skipped.
- Invalid database references fail the dataset load.
- Transactions are per dataset, not for the entire pipeline.
- Reconciliation detects inconsistencies after loading; it does not undo loads.
- Files are read into memory.
- Rejection reports and database transactions are separate operations.
- Payment events and order-status history are not stored.
- The project is a local learning implementation.

## Learning outcomes

CSV ingestion, Python validation, SQL relationships, decimal arithmetic,
transactions, upserts, source version handling, testing, logging,
continuous integration, and reconciliation.

## Later stages

- Build an analytics warehouse with dbt.
- Introduce scheduling and orchestration with Airflow.
- Extend reporting and operational monitoring.