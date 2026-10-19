select
    i.order_id,
    i.line_number,
    o.customer_id,
    i.product_id,
    o.order_date,
    o.order_status,
    o.source_updated_at,
    i.quantity,
    i.unit_price_eur,
    i.quantity * i.unit_price_eur as line_value_eur

from {{ ref('stg_order_items') }} as i

join {{ ref('stg_orders') }} as o
    on i.order_id = o.order_id