# Retail Data Platform

A data engineering learning project that turns synthetic retail CSV files
into validated PostgreSQL data and tested analytics models.

The project covers ingestion, relational modelling, data quality,
warehouse transformations, reporting, and continuous integration.

## How it works

1. Read customers, products, orders, and order items from CSV.
2. Validate records and save rejection reasons.
3. Load valid records into PostgreSQL.
4. Check that order totals match their item totals.
5. Build staging views, dimensions, a fact table, and a sales report with dbt.
6. Test the data and reconcile reporting totals.

## Tools

Python, PostgreSQL, Docker Compose, Psycopg, python-dotenv,
unittest, dbt Core, Git, GitHub, and GitHub Actions.

## Source data model

| Table | One row represents |
|---|---|
| customers | One customer |
| products | One product |
| orders | One order |
| order_items | One line within an order |

Foreign keys connect orders to customers and item lines to orders
and products.

The selling price is stored on each item line independently of the
product's current catalogue price.

## Ingestion features

- Required-field, date, status, quantity, and money validation.
- Python Decimal for monetary values.
- Timezone-aware source timestamps normalised to UTC.
- JSON rejection reports with original values and reasons.
- Timestamped progress and error logs.
- One transaction per dataset load.
- Duplicate protection through primary keys.
- Newer-version updates for orders.
- Reconciliation of stored order and item totals.

### Existing-record policies

| Dataset | Policy |
|---|---|
| Customers | Skip existing IDs |
| Products | Skip existing IDs |
| Orders | Accept newer source versions |
| Order items | Skip existing order ID and line-number pairs |

Equal or older order versions are skipped. This prevents stale deliveries
from overwriting newer order information.

## Analytics warehouse

dbt builds the following models in the analytics schema.

| Layer | Models | Purpose |
|---|---|---|
| Staging | stg_customers, stg_products, stg_orders, stg_order_items | Consistent source representation |
| Dimensions | dim_customers, dim_products | Current descriptive attributes |
| Fact | fct_order_items | Quantities and selling values per order line |
| Reporting | rpt_product_sales | Completed sales grouped by product |

Staging models are views. Dimensions, the fact model, and the report
are tables refreshed by dbt builds.

The warehouse uses business IDs as dimension keys and represents current
attributes and order status rather than historical versions.

## Sample data and results

All source records are synthetic.

| Dataset | Records |
|---|---:|
| Customers | 3 |
| Products | 5 |
| Source orders | 8 |
| Valid orders | 5 |
| Rejected orders | 3 |
| Order items | 10 |

The three rejected orders contain a negative amount, an invalid date,
and an unsupported status.

| Order-status total | Value |
|---|---:|
| Completed | €199.99 |
| Refunded | €74.90 |
| Cancelled | €35.50 |
| All statuses | €310.39 |

All five order totals match their item totals.

The product-sales report uses historical selling prices and includes
only orders currently marked completed. Its total reconciles to €199.99.

These values are order-status measures, not accounting revenue or
payment-event history.

## Testing and continuous integration

Python tests cover validation, duplicate deliveries, order corrections,
stale updates, foreign keys, historical selling prices, rollback,
and reconciliation outcomes.

dbt tests check required values, unique keys, relationships, allowed
statuses, fact totals, and reporting totals.

GitHub Actions is configured to:

- Create a temporary PostgreSQL database.
- Apply schema migrations.
- Run Python tests.
- Load and replay the sample files.
- Run ingestion reconciliation.
- Build and test the dbt warehouse.

## Project files

| Location | Purpose |
|---|---|
| src/ | Python ingestion and reconciliation |
| data/raw/ | Synthetic source files |
| sql/ | Schema migrations and SQL reports |
| tests/ | Python unit and integration tests |
| warehouse/models/ | dbt staging, warehouse, and reporting models |
| warehouse/tests/ | Custom SQL data tests |
| .github/workflows/tests.yml | Automated checks |

## Current limitations

- Customer, product, and item corrections are not applied.
- Equal order timestamps with conflicting values are skipped.
- Invalid database references fail the dataset load.
- Transactions are per dataset, not across the whole pipeline.
- Reconciliation detects inconsistencies after loading without undoing loads.
- Files are read into memory.
- Rejection reports are replaced each run.
- Source status and attribute history are not retained.
- Warehouse tables require a new dbt build after ingestion changes.
- Separate shipping fees, additional taxes, and order-level discounts
  are outside the sample model.
- This is a learning implementation rather than a production deployment.

## Learning outcomes

Reliable batch ingestion, relational modelling, SQL joins and aggregation,
transactions, version-aware upserts, dimensional modelling, dbt,
automated testing, reconciliation, and continuous integration.

## Later improvements

- Airflow scheduling and orchestration.
- Historical dimension tracking.
- More complete correction policies.
- Monitoring, log rotation, and run identifiers.
- Separate database roles with narrower permissions.