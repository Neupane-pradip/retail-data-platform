BEGIN;

CREATE TABLE public.products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    current_price NUMERIC(12, 2) NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT products_id_not_blank
        CHECK (length(trim(product_id)) > 0),

    CONSTRAINT products_name_not_blank
        CHECK (length(trim(product_name)) > 0),

    CONSTRAINT products_category_not_blank
        CHECK (length(trim(category)) > 0),

    CONSTRAINT products_price_valid
        CHECK (
            current_price >= 0
            AND current_price <> 'NaN'::numeric
        )
);

COMMIT;