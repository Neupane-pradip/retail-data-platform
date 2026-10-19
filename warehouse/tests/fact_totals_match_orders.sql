with fact_totals as (
    select
        order_id,
        sum(line_value_eur) as fact_amount_eur
    from {{ ref('fct_order_items') }}
    group by order_id
)

select
    o.order_id,
    o.order_amount_eur,
    f.fact_amount_eur

from {{ ref('stg_orders') }} as o

left join fact_totals as f
    on o.order_id = f.order_id

where
    f.order_id is null
    or o.order_amount_eur <> f.fact_amount_eur