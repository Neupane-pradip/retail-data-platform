BEGIN;

ALTER TABLE public.orders
    ADD COLUMN source_updated_at TIMESTAMPTZ;

COMMENT ON COLUMN public.orders.source_updated_at IS
    'Time the source system last modified this order; NULL means unknown.';

COMMIT;