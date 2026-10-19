select
    product_id,
    product_name,
    category,
    current_price as current_price_eur,
    loaded_at
from {{ source('retail', 'products') }}
