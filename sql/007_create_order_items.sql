BEGIN;

CREATE TABLE public.order_items (
    order_id TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT order_items_pk
        PRIMARY KEY (order_id, line_number),

    CONSTRAINT order_items_order_fk
        FOREIGN KEY (order_id)
        REFERENCES public.orders (order_id),

    CONSTRAINT order_items_product_fk
        FOREIGN KEY (product_id)
        REFERENCES public.products (product_id),

    CONSTRAINT order_items_line_number_positive
        CHECK (line_number > 0),

    CONSTRAINT order_items_quantity_positive
        CHECK (quantity > 0),

    CONSTRAINT order_items_unit_price_valid
        CHECK (
            unit_price >= 0
            AND unit_price <> 'NaN'::numeric
        )
);

COMMIT;