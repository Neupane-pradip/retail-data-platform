select
    order_id,
    customer_id,
    order_date,
    total_amount as order_amount_eur,
    status as order_status,
    source_updated_at,
    loaded_at
from {{ source('retail', 'orders') }}