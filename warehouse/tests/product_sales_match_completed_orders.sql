with reported as (
    select
        coalesce(sum(completed_sales_eur), 0) as reported_total
    from {{ ref('rpt_product_sales') }}
),

expected as (
    select
        coalesce(sum(order_amount_eur), 0) as expected_total
    from {{ ref('stg_orders') }}
    where order_status = 'completed'
)

select
    reported.reported_total,
    expected.expected_total
from reported
cross join expected
where reported.reported_total <> expected.expected_total