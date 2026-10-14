# Retail Data Platform

A data engineering learning project that turns retail order files into
validated data stored in PostgreSQL.

The goal is to build a pipeline that handles invalid records, repeated
files, and corrected orders.

## How it works

1. Read orders from a CSV file.
2. Validate required fields, dates, amounts, and statuses.
3. Save rejected records and their reasons to a JSON file.
4. Insert new orders into PostgreSQL.
5. Update existing orders when their values change.
6. Skip records that already match the database.
7. Record progress and errors in a log file.

All database changes from one load are committed together. If a database
operation fails, the transaction is rolled back.

## Tools

- Python — extraction, validation, and loading
- PostgreSQL — data storage and SQL queries
- Docker Compose — local database environment
- Psycopg — Python connection to PostgreSQL
- unittest — automated tests
- Git and GitHub — version control

## Project structure

| Location | Purpose |
|---|---|
| `src/` | Pipeline code |
| `data/raw/orders.csv` | Synthetic sample orders |
| `data/rejected/` | Generated rejection reports |
| `sql/` | Database table definitions |
| `tests/` | Validation and database tests |
| `logs/` | Generated pipeline logs |
| `compose.yml` | PostgreSQL container configuration |
| `.env.example` | Example configuration without real credentials |

## Order rules

Each row represents one order. All amounts are in EUR.

- Order and customer IDs must not be empty.
- Dates must use the valid `YYYY-MM-DD` format.
- Amounts must be finite, non-negative, and representable in whole cents.
- Status must be `completed`, `cancelled`, or `refunded`.
- A refunded order keeps its original amount.

## Setup

Run these commands from the project root on Windows.

### 1. Create a Python environment

```powershell
python -m venv .venv
```

### 2. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configure the connection

```powershell
Copy-Item .env.example .env
```

Edit `.env` with your local settings:

```dotenv
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_USER=retail_user
POSTGRES_PASSWORD=replace_with_your_local_password
POSTGRES_DB=retail_db
```

Keep `.env` out of Git.

### 4. Start PostgreSQL

Open Docker Desktop, then run:

```powershell
docker compose up -d
docker compose ps
```

Wait until PostgreSQL reports `healthy`.

### 5. Create the table

Run once for a new database:

```powershell
docker compose cp sql/001_create_orders.sql postgres:/tmp/001_create_orders.sql
```

```powershell
docker compose exec postgres psql -U retail_user -d retail_db -v ON_ERROR_STOP=1 -f /tmp/001_create_orders.sql
```

## Run the pipeline

```powershell
.\.venv\Scripts\python.exe src/main.py
```

The output reports records read, valid, rejected, inserted or updated,
and unchanged.

- Rejection report: `data/rejected/orders_rejected.json`
- Log file: `logs/pipeline.log`

The rejection report is replaced each run. Logs are appended.

## Run tests

Validation tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

To also run the database rollback test, keep PostgreSQL running and use:

```powershell
$env:RUN_DB_TESTS = "1"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:RUN_DB_TESTS
```

## Query the data

Connect:

```powershell
docker compose exec postgres psql -U retail_user -d retail_db
```

View orders:

```sql
SELECT order_id, order_date, total_amount, status
FROM public.orders
ORDER BY order_id;
```

Calculate completed-order value by date:

```sql
SELECT
    order_date,
    SUM(total_amount) AS completed_order_value
FROM public.orders
WHERE status = 'completed'
GROUP BY order_date
ORDER BY order_date;
```

Exit with `\q`.

## Current limitations

- Incoming records overwrite different values for the same order ID.
  Older files can therefore overwrite newer information.
- Files are read into memory.
- The rejection report and database changes are separate operations.
- This is a local learning environment, not a production deployment.

## What this project teaches

CSV ingestion, Python validation, decimal arithmetic, SQL constraints,
transactions, upserts, repeatable loading, logging, and automated testing.

## Next improvements

- Prevent older records from overwriting newer updates.
- Add automated tests for order corrections.
- Extend the model with customers, products, and order items.