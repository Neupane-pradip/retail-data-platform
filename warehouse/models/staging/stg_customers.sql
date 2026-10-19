select
    customer_id,
    customer_name,
    city,
    loaded_at
from {{ source('retail', 'customers') }}