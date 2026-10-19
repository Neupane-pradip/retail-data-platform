select
    product_id,
    product_name,
    category,
    current_price_eur
from {{ ref('stg_products') }}