select
    p.product_id,
    p.product_name,
    p.category,
    count(distinct f.order_id) as completed_order_count,
    sum(f.quantity) as units_sold,
    sum(f.line_value_eur) as completed_sales_eur

from {{ ref('fct_order_items') }} as f

join {{ ref('dim_products') }} as p
    on f.product_id = p.product_id

where f.order_status = 'completed'

group by
    p.product_id,
    p.product_name,
    p.category