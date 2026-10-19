select
    order_id,
    line_number,
    count(*) as duplicate_count
from {{ ref('fct_order_items') }}
group by
    order_id,
    line_number
having count(*) > 1