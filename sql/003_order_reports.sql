-- Report 1: Number and value of orders by current status.
SELECT
    status,
    COUNT(*) AS order_count,
    SUM(total_amount) AS order_value_eur
FROM public.orders
GROUP BY status
ORDER BY status;


-- Report 2: Daily summary grouped by original order date.
SELECT
    order_date,
    COUNT(*) AS total_orders,

    COUNT(*) FILTER (
        WHERE status = 'completed'
    ) AS completed_orders,

    COUNT(*) FILTER (
        WHERE status = 'cancelled'
    ) AS cancelled_orders,

    COUNT(*) FILTER (
        WHERE status = 'refunded'
    ) AS refunded_orders,

    COALESCE(
        SUM(total_amount) FILTER (
            WHERE status = 'completed'
        ),
        0
    ) AS completed_value_eur,

    COALESCE(
        SUM(total_amount) FILTER (
            WHERE status = 'refunded'
        ),
        0
    ) AS refunded_value_eur

FROM public.orders
GROUP BY order_date
ORDER BY order_date;


-- Report 3: Overall control totals.
SELECT
    COUNT(*) AS total_orders,
    COUNT(DISTINCT customer_id) AS distinct_customers,
    SUM(total_amount) AS total_order_value_eur,

    COUNT(*) FILTER (
        WHERE source_updated_at IS NULL
    ) AS orders_missing_source_timestamp

FROM public.orders;