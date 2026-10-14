CREATE TABLE public.orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    order_date DATE NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL,
    status TEXT NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT orders_order_id_not_blank
        CHECK (length(trim(order_id)) > 0),

    CONSTRAINT orders_customer_id_not_blank
        CHECK (length(trim(customer_id)) > 0),

    CONSTRAINT orders_amount_valid
        CHECK (
            total_amount >= 0
            AND total_amount <> 'NaN'::numeric
        ),

    CONSTRAINT orders_status_valid
        CHECK (status IN ('completed', 'cancelled', 'refunded'))
);