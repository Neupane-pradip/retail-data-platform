BEGIN;

CREATE TABLE public.customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    city TEXT NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT customers_id_not_blank
        CHECK (length(trim(customer_id)) > 0),

    CONSTRAINT customers_name_not_blank
        CHECK (length(trim(customer_name)) > 0),

    CONSTRAINT customers_city_not_blank
        CHECK (length(trim(city)) > 0)
);

COMMIT;