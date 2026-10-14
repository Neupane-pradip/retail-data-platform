# Retail Data Platform

A learning project that loads retail orders from CSV into PostgreSQL
using Python.

The pipeline validates records, saves rejected records with their reasons,
and inserts valid orders without creating duplicate order IDs.

## Pipeline

CSV → Python validation → rejection report + PostgreSQL → SQL queries

One input row represents one order. All monetary amounts are in EUR.

## Current features

- Read orders from a CSV file.
- Convert dates to Python `date` values and amounts to `Decimal`.
- Validate required fields, dates, amounts, and statuses.
- Save invalid records and rejection reasons to JSON.
- Store valid orders in PostgreSQL.
- Skip order IDs already stored in the database.
- Load valid orders in a single database transaction.
- Run automated tests for order validation.

## Tools

- Python
- PostgreSQL 18
- Docker Desktop and Docker Compose
- Psycopg 3
- python-dotenv
- unittest
- Git and GitHub

## Project structure

```text
retail-data-platform/
├── data/
│   ├── raw/
│   │   └── orders.csv
│   └── rejected/                 # Generated; ignored by Git
├── sql/
│   └── 001_create_orders.sql
├── src/
│   ├── main.py
│   ├── extract.py
│   ├── validate.py
│   ├── reject.py
│   └── load.py
├── tests/
│   └── test_validate.py
├── .env                         # Local settings; ignored by Git
├── .env.example
├── .gitignore
├── compose.yml
├── requirements.txt
└── README.md
```

## Order validation rules

| Field | Rule |
|---|---|
| `order_id` | Required and non-empty |
| `customer_id` | Required and non-empty |
| `order_date` | Valid date in `YYYY-MM-DD` format |
| `total_amount` | Finite, non-negative, and representable in whole cents |
| `status` | `completed`, `cancelled`, or `refunded` |

Surrounding whitespace is removed from required values.
Statuses are converted to lowercase.

Refunded orders retain their original amount. Their status identifies
them as refunded.

## Local setup

### 1. Clone the repository

```powershell
git clone https://github.com/Neupane-pradip/retail-data-platform.git
cd retail-data-platform
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

The following commands use the virtual environment's Python directly,
so activating it is optional.

### 3. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Configure the database connection

Create a local configuration file:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

```dotenv
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_USER=retail_user
POSTGRES_PASSWORD=replace_with_your_local_password
POSTGRES_DB=retail_db
```

Replace the password placeholder. Do not commit `.env`.

The Docker database uses host port `5433` and container port `5432`,
allowing it to run alongside a typical local PostgreSQL installation.

### 5. Start PostgreSQL

Ensure Docker Desktop is running, then execute:

```powershell
docker compose up -d
docker compose ps
```

Wait until the PostgreSQL service reports `healthy`.

Database files are stored in a persistent Docker volume.

### 6. Create the orders table

Run these commands once for a new database:

```powershell
docker compose cp sql/001_create_orders.sql postgres:/tmp/001_create_orders.sql
```

```powershell
docker compose exec postgres psql -U retail_user -d retail_db -v ON_ERROR_STOP=1 -f /tmp/001_create_orders.sql
```

The schema script creates `public.orders`. It is not intended to be
rerun against an existing table.

## Run the pipeline

From the project root:

```powershell
.\.venv\Scripts\python.exe src/main.py
```

For an empty orders table and the supplied sample containing five valid
and three invalid records, the summary is:

```text
Orders read: 8
Valid orders: 5
Rejected orders: 3
Orders inserted: 5
Existing order IDs skipped: 0
```

Running the same input again produces:

```text
Orders inserted: 0
Existing order IDs skipped: 5
```

Rejected records are written to:

```text
data/rejected/orders_rejected.json
```

This report is replaced on each run. If no records are rejected,
it contains an empty JSON array.

## Run validation tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The tests cover valid conversions and rejection scenarios such as
invalid dates, negative amounts, fractions of a cent, non-finite
amounts, and unsupported statuses.

## Inspect stored orders

Connect to PostgreSQL:

```powershell
docker compose exec postgres psql -U retail_user -d retail_db
```

Run:

```sql
SELECT
    order_id,
    customer_id,
    order_date,
    total_amount,
    status
FROM public.orders
ORDER BY order_id;
```

Count stored orders:

```sql
SELECT COUNT(*) AS order_count
FROM public.orders;
```

Query completed-order value by date:

```sql
SELECT
    order_date,
    SUM(total_amount) AS completed_order_value
FROM public.orders
WHERE status = 'completed'
GROUP BY order_date
ORDER BY order_date;
```

Exit psql with `\q`.

## Reliability and current limitations

- `order_id` is the table's primary key.
- Existing order IDs are skipped using `ON CONFLICT DO NOTHING`.
- Corrections to an existing order are not applied yet.
- Valid orders from one loader call are committed together.
  A database error rolls back that transaction.
- Database constraints enforce required values, supported statuses,
  and valid stored amounts.
- Python rejects fractional cents before loading; PostgreSQL's
  `NUMERIC(12,2)` type can otherwise round extra decimal places.
- The rejection report is separate from the database transaction.
- Files are currently read into memory.
- The setup is intended for local learning and uses the database's
  initial administrative role.

## Stop the database

```powershell
docker compose stop
```

Restart it with:

```powershell
docker compose start
```

`docker compose down` removes containers and the project network while
preserving the named database volume. Adding `-v` also deletes that volume
and its stored data.

## Next steps

- Verify rollback behaviour with a deliberate loading failure.
- Add database integration tests.
- Introduce structured logging.
- Define how corrected and late-arriving orders should be handled.
- Extend the data model with customers, products, and order items.