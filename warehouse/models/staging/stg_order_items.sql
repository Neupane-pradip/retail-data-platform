select
    order_id,
    line_number,
    product_id,
    quantity,
    unit_price as unit_price_eur,
    loaded_at
from {{ source('retail', 'order_items') }}