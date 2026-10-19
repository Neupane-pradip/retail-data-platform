BEGIN;

ALTER TABLE public.orders
    ADD CONSTRAINT orders_customer_fk
    FOREIGN KEY (customer_id)
    REFERENCES public.customers (customer_id);

COMMIT;